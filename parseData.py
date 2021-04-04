"""
Will be a pretty long file for taking TT data from a list of location sources, fetching all trains within a window,
parsing them and creating Json TTs to put into a DB. This file will pass back a list of Json TTs for parsing.
"""
import requests
from bs4 import BeautifulSoup
import re
import common
from customLocationLogic import CustomLogicExecutor

CAPITALS = 'ABCDEFGHIJ'

def parse_location_times(times_string: str) -> dict:
    formatted_times_string = times_string.replace('&half', '.5')
    dep = re.match('.*d\\. (\\d{2}:\\d{2}(?:\\.5)?)', formatted_times_string)
    arr = re.match('.*a\\. (\\d{2}:\\d{2}(?:\\.5)?)', formatted_times_string)
    pas = re.match('.*p\\. (\\d{2}:\\d{2}(?:\\.5)?)', formatted_times_string)

    if dep is not None and arr is None:
        return {'dep': dep.group(1).replace(':', ''), 'isOrigin': 'yes'}
    if dep is not None and arr is not None:
        return {'dep': dep.group(1).replace(':', ''), 'arr': arr.group(1).replace(':', '')}
    if dep is None and arr is not None:
        return {'arr': arr.group(1).replace(':', '')}
    if pas is not None:
        return {'dep': pas.group(1).replace(':', '')}


def parse_allowances(allow_string: str) -> dict:
    out = {}
    formatted_allow_string = allow_string.replace('½', '.5')
    prf_allow = re.match('Perf: (\\d+(?:\\.5)?)', formatted_allow_string)
    pth_allow = re.match('Path: (\\d+(?:\\.5)?)', formatted_allow_string)
    eng_allow = re.match('Eng: (\\d+(?:\\.5)?)', formatted_allow_string)

    if prf_allow is not None:
        out['prf allow'] = prf_allow.group(1)
    if pth_allow is not None:
        out['pth allow'] = pth_allow.group(1)
    if eng_allow is not None:
        out['eng allow'] = eng_allow.group(1)

    return out


def parse_sched_table(table) -> list:
    """
    :param table: BeautifulSoup instance of the sched-table
    :return: list of locations for the train to then tidy up with futher logic. Example location keys
     { 'Location', 'dep', 'arr', 'path', 'line', 'plat', 'pth allow', .. , 'Activities' }
    """
    n_columns = 0
    n_rows = 0
    column_names = []

    # Find number of rows and columns
    # we also find the column titles if we can
    for row in table.find_all('tr'):

        # Handle column names if we find them
        th_tags = row.find_all('th')
        if len(th_tags) > 0 and len(column_names) == 0:
            for th in th_tags:
                column_names.append(th.get_text())

        else:
            # Determine the number of rows in the table
            td_tags = row.find_all('td')
            if len(td_tags) > 0:
                n_rows += 1
                if n_columns == 0:
                    # Set the number of columns for our table
                    n_columns = len(td_tags)

    # Safeguard on Column Titles
    if len(column_names) > 0 and len(column_names) != n_columns:
        raise Exception("Column titles do not match the number of columns")

    column_names = column_names if len(column_names) > 0 else range(0, n_columns)
    df = []
    row_marker = 0
    for row in table.find_all('tr'):
        row_to_add = {}
        column_marker = 0
        columns = row.find_all('td')
        if len(columns) != n_columns:
            continue
        for column in columns:

            a_tag = column.find('a')
            if a_tag is not None and 'href' in a_tag.attrs:
                tiploc = re.match('.*/sum/([A-Z0-9]+)/.*', a_tag['href']).group(1)
                row_to_add[column_names[column_marker]] = tiploc

            elif 'Times WTT(Public)' in column_names[column_marker]:
                times = parse_location_times(column.get_text())
                for time in times.keys():
                    row_to_add[str(time)] = times[time]

            elif 'Plat' in column_names[column_marker]:
                if column.get_text() != '':
                    row_to_add['plat'] = column.get_text()

            elif 'Path-Line' in column_names[column_marker]:
                col_text = column.get_text()
                if col_text != '':
                    split_col = col_text.split(' - ')
                    if split_col[0] != '':
                        row_to_add['path'] = split_col[0]
                    if split_col[1] != '':
                        row_to_add['line'] = split_col[1]

            elif 'Allowances' in column_names[column_marker]:
                allowances = parse_allowances(column.get_text())
                for allowance in allowances.keys():
                    row_to_add[str(allowance)] = allowances[allowance]

            elif 'Activities' in column_names[column_marker]:
                if column.get_text() != '':
                    row_to_add[column_names[column_marker]] = column.get_text().split('.')[:-1]

            column_marker += 1

        df.append(row_to_add)
        if len(columns) > 0:
            row_marker += 1

    return df


def parse_train_table(train_info_table) -> dict:
    """
    :param train_info_table: BeautifulSoup instance of the ch train info table.
    :return: map like: { uid, operator_code, headcode?, Train category?, Power type?, Timing Load?, max_speed?, Train Status? }
    """
    rows_interested_in = ['Train UID', 'ATOC code', 'Signalling ID', 'Train category', 'Power type', 'Timing Load',
                          'Speed', 'Train Status']
    out = {}
    for row in train_info_table.find_all('tr'):

        fields = row.find_all('td')
        row_name = fields[0].get_text()
        if row_name not in rows_interested_in:
            continue

        row_1 = fields[1].get_text()
        row_2 = fields[2].get_text()

        if row_name == 'Train UID':
            out['uid'] = row_1.replace('∇', 'V')

        if row_name == 'ATOC code':
            if row_1 not in ['', ' ']:
                out['operator_code'] = row_1
            else:
                out['operator_code'] = 'ZZ'

        if row_name == 'Signalling ID':
            if row_1 not in ['', ' ']:
                out['headcode'] = row_1

        if row_name == 'Train category':
            if row_1 not in ['', ' '] or row_2 not in ['', ' ']:
                out['Train_category'] = row_1 + ' ' + row_2

        if row_name == 'Power type':
            if row_1 not in ['', ' ']:
                out['Power_type'] = row_1

        if row_name == 'Timing Load':
            if row_1 not in ['', ' '] or row_2 not in ['', ' ']:
                out['Timing_Load'] = row_1 + ' ' + row_2

        if row_name == 'Speed':
            if re.search('\\d+', row_1.strip()) is not None:
                out['max_speed'] = row_1

        if row_name == 'Train Status':
            if 'passenger' in row_2.lower():
                out['is_freight'] = '0'
            else:
                out['is_freight'] = '-1'
                out['can_use_goods_lines'] = '-1'
            if row_1 not in ['', ' ']:
                out['Train_Status'] = row_2

    return out


def parse_train_header(header_text: str) -> dict:
    """
    :param header_text: text in charlwoodhouse train page header.
    :return: map { 'ch_id', 'origin_time', 'origin_name', 'dest_name' }
    """
    match = re.match('Train (\\d+) \\(.+\\) (?:[0-9][A-Z][0-9]{2})? (\\d{2}:\\d{2}) (.+) to (.+)', header_text)

    return {'ch_id': match.group(1), 'origin_time': match.group(2).replace(':', ''), 'origin_name': match.group(3),
            'destination_name': match.group(4)}


def refine_headcode(train_info: dict) -> str:
    if 'max_speed' in train_info:
        max_speed = train_info['max_speed']
        end_part = ''
        try:
            for digit in train_info['uid'][-3:]:
                end_part += CAPITALS[int(digit)]
        except:
            end_part = train_info['uid'][-3:]

        if max_speed in ['75', '075']:
            return f"4{end_part}"
        if max_speed in ['60', '060']:
            return f"6{end_part}"
        if max_speed in ['45', '045']:
            return f"7{end_part}"
        if max_speed in ['35', '035']:
            return f"8{end_part}"

    return train_info['uid'][:4]


def info_passes_field_criteria(field_name: str, field_criteria: dict, train_info: dict):
    if field_name not in train_info:
        return False

    value_in_info = train_info[field_name]

    if 'not' in field_criteria and len(list(filter(lambda x: x != value_in_info, field_criteria['not']))) > 0:
        return False

    return re.fullmatch(field_criteria['match'], value_in_info.strip()) is not None


def match_category(train_info: dict, categories_map: dict) -> list:
    for category in categories_map.keys():
        criteria = categories_map[category]['criteria']

        cat_match = True

        for field in criteria.keys():
            if info_passes_field_criteria(str(field), criteria[field], train_info) is False:
                cat_match = False
                break

        if cat_match is True:
            return [str(category), categories_map[category]]

    return ['standard diesel freight', categories_map['standard diesel freight']]


def complete_train_info(categories_map: dict, train_info: dict) -> dict:
    """
    :param categories_map: the train categories map.
    :param train_info: the train information scraped from source.
    :return: complete train info ready to become basis of train.
    """

    out = {}
    # stick in values we already know
    for prop in ['headcode', 'uid', 'is_freight', 'origin_name', 'origin_time', 'destination_name', 'operator_code',
                 'destination_time']:
        out[prop] = train_info[prop]

    category_name, matched_category = match_category(train_info, categories_map)

    out['category'] = category_name

    for prop in matched_category.keys():
        if 'criteria' in str(prop).lower() or 'id' in str(prop).lower():
            continue
        if str(prop) in train_info:
            out[str(prop)] = train_info[str(prop)]
        else:
            out[str(prop)] = matched_category[prop]

    # except:
    # start_traction, description
    out['start_traction'] = out['electrification']
    out['description'] = '$template'

    return out


def do_times_cross_midnight(location1: dict, location2: dict) -> bool:
    if location1['location'] == location2['location']:
        return False

    time1dep = ''
    time1arr = ''
    time2dep = ''
    time2arr = ''

    if 'dep' in location1:
        time1dep = location1['dep']
    if 'arr' in location1:
        time1arr = location1['arr']
    if 'dep' in location2:
        time2dep = location2['dep']
    if 'arr' in location2:
        time2arr = location2['arr']

    if time1dep != '':
        if time2dep != '':
            if float(time1dep) > float(time2dep):
                return True
        if time2arr != '':
            if float(time1dep) > float(time2arr):
                return True
    if time1arr != '':
        if time2dep != '':
            if float(time1arr) > float(time2dep):
                return True
        if time2arr != '':
            if float(time1arr) > float(time2arr):
                return True
    return False


def times_span_multiple_days(locations: list) -> bool:
    for i in range(len(locations) - 1):
        if do_times_cross_midnight(locations[i], locations[i + 1]) is True:
            return True
    return False


def remove_locations_before_0000(locations: list) -> list:
    # find point where location after
    remove_up_to = 0
    for i in range(len(locations) - 1):
        if do_times_cross_midnight(locations[i], locations[i + 1]) is True:
            remove_up_to = i + 1

    return locations[remove_up_to:]


def add_time_to_locations_after_0000(locations: list) -> list:
    add_24h = 0
    for i in range(len(locations) - 1):
        if do_times_cross_midnight(locations[i], locations[i + 1]) is True:
            add_24h = i + 1

    for i in range(add_24h, len(locations)):
        if 'dep' in locations[i]:
            locations[i]['dep'] = common.convert_sec_to_time(
                common.convert_time_to_secs(locations[i]['dep']) + common.convert_time_to_secs('2400'))
        if 'arr' in locations[i]:
            locations[i]['arr'] = common.convert_sec_to_time(
                common.convert_time_to_secs(locations[i]['arr']) + common.convert_time_to_secs('2400'))

    return locations

def convert_train_locations(initial_locations: list, location_maps: list, source_location: str) -> list:
    """
    :param initial_locations: the list of locations scraped from source.
    :param location_maps: the entry and sim location maps
    :param source_location: used if we have times spanning more than one day.
    :return: [ readable list of locations on sim, the potential entry point for the train ]
    """
    # get the map of sim locations
    [entry_points, locations_map] = location_maps

    # create list of entry point names
    list_of_entry_points = []
    for lis in entry_points.values():
        for elt in lis:
            list_of_entry_points.append(elt)

    # for each location check if potential entry point then check if in locations (both sides)
    potential_entry_point = None
    new_locations = []
    for location in initial_locations:
        if 'Activities' in location:
            if 'Stops to change trainmen' in location['Activities']:
                location['activities'] = {"crewChange": ""}

        if location['Location'] in list_of_entry_points and potential_entry_point is None:
            for entry_point in entry_points.keys():
                if location['Location'] in entry_points[entry_point]:
                    potential_entry_point = entry_point

        # check l keys
        loc = common.find_readable_location(location['Location'], locations_map)
        if loc != '':
            location['location'] = loc
            new_locations.append(location)
            location.pop('Location')
            continue

        # check l values
        loc = common.find_tiploc_for_location(location['Location'], locations_map)
        if loc != '':
            location['location'] = locations_map[loc]
            location.pop('Location')
            new_locations.append(location)
            continue

    if times_span_multiple_days(new_locations) is True:
        readable_source_location = common.find_readable_location(source_location)
        location_on_day = list(filter(lambda x: x['location'] == readable_source_location, new_locations))[0]

        if do_times_cross_midnight(new_locations[0], location_on_day):
            new_locations = remove_locations_before_0000(new_locations)
        elif do_times_cross_midnight(location_on_day, new_locations[-1]):
            new_locations = add_time_to_locations_after_0000(new_locations)

    return [new_locations, potential_entry_point]


def Parse_Charlwood_Train(sim_id: str, categories_map: dict, location_maps: list, custom_logic: CustomLogicExecutor,
                          source_location: str, **kwargs):
    """

    :param sim_id:
    :param categories_map:
    :param location_maps:
    :param custom_logic:
    :param source_location:
    :param kwargs: Contains either 'train_filepath' if parsing from file or 'train_link' if parsing from page
    :return:
    """
    if 'train_filepath' in kwargs:
        train_file_as_string = ''

        f = open(kwargs['train_filepath'], "r")
        # f = open('assorted_files/charlwoodhousesimsig/charlwoodhouse.co.uk/rail/liverail/train/16596143/14/02/20.html', "r")
        for file_line in f:
            train_file_as_string += file_line.rstrip()
        f.close()

        train_page = BeautifulSoup(train_file_as_string, 'html.parser')
    elif 'train_link' in kwargs:
        response = requests.get(kwargs['train_link'])
        train_page = BeautifulSoup(response.content, 'html.parser')
    else:
        print('No train passed in')
        return None

    # Fetch ch id and origin time location and dest from top of page <h2>
    header_data = parse_train_header(train_page.find('h2').get_text())
    print(f"parsing train {header_data['origin_time']} {header_data['origin_name']} - {header_data['destination_name']}")

    # Fetch train info from train table
    train_info = parse_train_table(train_page.find('table', {'class': 'train-table'}))

    train_info['origin_name'] = header_data['origin_name']
    train_info['origin_time'] = header_data['origin_time']
    train_info['destination_name'] = header_data['destination_name']

    # Sort headcode
    if 'headcode' not in train_info:
        train_info['headcode'] = refine_headcode(train_info)

    # Fetch location data from sched table
    initial_locations = parse_sched_table(train_page.find('table', {'class': 'sched-table'}))

    if 'arr' in initial_locations[-1]:
        train_info['destination_time'] = initial_locations[-1]['arr']
    else:
        train_info['destination_time'] = initial_locations[-1]['dep']

    # Work out other fields for train from train cat dict
    train_info = complete_train_info(categories_map, train_info)

    # Filter locations out via sim locations and translate TIPLOC to readable
    [readable_locations, potential_entry_point] = convert_train_locations(initial_locations, location_maps,
                                                                          source_location)

    # Send locations in to sim specific location logic, **this will give entry point and time if applic.**
    entry_point, entry_time, tt_template, final_locations = custom_logic.Perform_Custom_Logic(readable_locations,
                                                                                              potential_entry_point)

    train_to_return = {}

    for field in train_info:
        train_to_return[field] = train_info[field]

    if entry_point is not None:
        train_to_return['entry_point'] = entry_point
        train_to_return['entry_time'] = entry_time

    train_to_return['tt_template'] = tt_template

    train_to_return['locations'] = final_locations

    return train_to_return


# Part of the file for parsing charlwoodhouse location pages.

def parse_summary_page(start_time: str, end_time: str, summary_page) -> list:
    """
    :param start_time: start of period to look for trains in format hhmm
    :param end_time: end of period to look for trains in format hhmm
    :param summary_page: the BeautifulSoup summary page.
    :return: list of links to train pages.
    """

    summary_tables = summary_page.find_all('table', class_='summ-table')

    list_of_times = []
    for summary_table in summary_tables:
        for row in summary_table.find_all('tr'):
            fields = row.find_all('td')
            if len(fields) == 4:
                formatted_times_field = fields[1].get_text().replace('&half', '.5').replace('\n', '')
                time_match_obj = re.search('(\\d{4}(?:\\.5)?)', formatted_times_field)
                if time_match_obj is not None:
                    list_of_times.append(
                        [float(time_match_obj.group(1)), fields[2].find('a')['href']])

    start_time_num = float(start_time)
    end_time_num = float(end_time)
    list_of_times = list(filter(lambda x: (x[0] >= start_time_num), list_of_times))
    list_of_times = list(filter(lambda x: (x[0] <= end_time_num), list_of_times))

    return [x[1] for x in list_of_times]


def parse_full_page(start_time: str, end_time: str, full_page) -> list:
    """
    :param start_time: start of period to look for trains in format hhmm
    :param end_time: end of period to look for trains in format hhmm
    :param full_page: the BeautifulSoup full page.
    :return: list of links to train pages.
    """
    tiploc_for_location = re.search('\\(([A-Z ]+)\\)', full_page.find('h2').get_text()).group(1).split(' ')[0]
    tables_on_page = full_page.find_all('table')

    locations_table = None

    for table in tables_on_page:
        if table.find('tr', {'class': 'small-table'}):
            locations_table = table
            break

    if locations_table is None:
        print('could not find locations table')
        return []

    list_of_times = []

    for row in locations_table.find_all('tr'):
        fields = row.find_all('td')
        if len(fields) > 0:
            formatted_times_field = fields[7].get_text().replace('&half', '.5').replace('\n', '')
            time_match_obj = re.match('.*(\\d{2}:\\d{2}(?:\\.5)?)', formatted_times_field)
            list_of_times.append(
                [float(time_match_obj.group(1).replace(':', '')), fields[0].find('a')['href']])

    start_time_num = float(start_time)
    end_time_num = float(end_time)
    list_of_times = list(filter(lambda x: (x[0] >= start_time_num), list_of_times))
    list_of_times = list(filter(lambda x: (x[0] <= end_time_num), list_of_times))

    return [tiploc_for_location, [x[1] for x in list_of_times]]


def Parse_Charlwood_House_Location_File(start_time: str, end_time: str, location_of_file: str) -> list:
    """
    :param start_time: start of period to look for trains in format hhmm
    :param end_time: end of period to look for trains in format hhmm
    :param location_of_file: relative path to charlwoodhouse locations file.
    :return: list of train ids to parse the individual files.
    """
    location_page_as_string = ''

    f = open(location_of_file, "r")
    for file_line in f:
        location_page_as_string += file_line.rstrip()
    f.close()

    if '/sum/' in location_of_file:
        print(f'Collecting trains for {location_of_file}')
        summary_page = BeautifulSoup(location_page_as_string, 'html.parser')
        list_of_links = parse_summary_page(start_time, end_time, summary_page)
        tiploc_location = re.search('/sum/([A-Z]+)/', location_of_file).group(1)

        return [tiploc_location, [re.match('.*/train/(\\d+)/.*', x).group(1) for x in list_of_links]]

    elif '/full/' in location_of_file:
        print(f'Collecting trains for {location_of_file}')
        full_page = BeautifulSoup(location_page_as_string, 'html.parser')
        tiploc_location, list_of_links = parse_full_page(start_time, end_time, full_page)

        return [tiploc_location, [re.match('.*/train/(\\d+)/.*', x).group(1) for x in list_of_links]]
    else:
        print('Could not determine location file type: ' + location_of_file)
        return []


def Parse_Charlwood_House_Location_Page(start_time: str, end_time: str, location_page_link: str) -> list:
    """
    :param start_time: start of period to look for trains in format hhmm
    :param end_time: end of period to look for trains in format hhmm
    :param location_page_link: relative path to charlwoodhouse locations page.
    :return: list of links to charlwoodhouse train pages.
    """

    response = requests.get(location_page_link)

    if '/sum/' in location_page_link:
        print(f'Collecting trains for {location_page_link}')
        summary_page = BeautifulSoup(response.content, 'html.parser')
        list_of_links = parse_summary_page(start_time, end_time, summary_page)
        tiploc_location = re.search('/sum/([A-Z]+)/', location_page_link).group(1)

        return [tiploc_location, [f'http://charlwoodhouse.co.uk{x}' for x in list_of_links]]

    elif '/full/' in location_page_link:
        print(f'Collecting trains for {location_page_link}')
        full_page = BeautifulSoup(response.content, 'html.parser')
        tiploc_location, list_of_links = parse_full_page(start_time, end_time, full_page)

        return [tiploc_location, [f'http://charlwoodhouse.co.uk{x}' for x in list_of_links]]
    else:
        print('Could not determine location page type: ' + location_page_link)
        return []


def Parse_Rtt_Location_Page(start_time: str, end_time: str, location_page_link: str):
    return None


def Parse_Rtt_Train(sim_id: str, train_cat, location_maps, custom_logic: CustomLogicExecutor, source_location: str,
                    **kwargs):
    return None

# print(parse_charlwood_house_location_page('0400', '2400', 'http://charlwoodhouse.co.uk/rail/liverail/full/sdon/26/03/20'))
# a = common.create_location_map_from_file('newport')
# parse_charlwood_train('newport', None, CustomLogicExecutor('newport', a[1], a[0]),
#                       train_link='http://www.charlwoodhouse.co.uk/rail/liverail/train/22449918/01/04/21')