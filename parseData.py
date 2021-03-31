"""
Will be a pretty long file for taking TT data from a list of location sources, fetching all trains within a window,
parsing them and creating Json TTs to put into a DB. This file will pass back a list of Json TTs for parsing.
"""
import requests
from bs4 import BeautifulSoup
import re
import common


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
            out['uid'] = row_1

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
            if row_1 not in ['', ' ']:
                out['max_speed'] = int(row_1)

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

        if max_speed == 75:
            return f"4{train_info['uid'][:3]}"
        if max_speed == 60:
            return f"6{train_info['uid'][:3]}"
        if max_speed == 45:
            return f"7{train_info['uid'][:3]}"
        if max_speed == 35:
            return f"8{train_info['uid'][:3]}"

    return train_info['uid'][:4]


def info_passes_field(field_name: str, field_criteria: dict, train_info: dict):
    if field_name not in train_info:
        return False

    value_in_info = train_info[field_name]

    if 'not' in field_criteria and len(list(filter(lambda x: x != value_in_info, field_criteria['not']))) > 0:
        return False

    return re.fullmatch(field_criteria['match'], value_in_info.strip()) is not None


def match_category(train_info: dict, categories_map: dict) -> list :

    for category in categories_map.keys():
        criteria = categories_map[category]['criteria']

        cat_match = True

        for field in criteria.keys():
            if info_passes_field(str(field), criteria[field], train_info) is False:
                cat_match = False
                break

        if cat_match is True:
            return [str(category), categories_map[category]]

    return ['standard diesel freight', categories_map['standard diesel freight']]


def complete_train_info(sim_id: str, train_info: dict) -> dict:
    """
    :param sim_id: temporarily provided, will be categories map.
    :param train_info: the train information scraped from source.
    :return: complete train info ready to become basis of train.
    """
    # TODO make this an instance variable to pass in
    categories_map = common.create_categories_map_from_yaml('templates/train_categories/default_categories_map.yaml')

    out = {}
    # stick in values we already know
    for prop in ['headcode', 'uid', 'is_freight', 'origin_name', 'origin_time', 'destination_name', 'operator_code']:
        out[prop] = train_info[prop]

    category_name, matched_category = match_category(train_info, categories_map)

    out['category'] = category_name

    for prop in matched_category.keys():
        if 'criteria' in str(prop).lower():
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


def convert_train_locations(sim_id: str, initial_locations: list) -> list:
    """
    :param sim_id: temporarily provided, will be locations and entry point map.
    :param initial_locations: the list of locations scraped from source.
    :return: [ readable list of locations on sim, the potential entry point for the train ]
    """
    # TODO move map creation out to main file so we are not doing this every time.
    # get the map of sim locations
    [entry_points, locations_map] = common.create_location_map_from_file(sim_id)

    # create list of entry point names
    list_of_entry_points = []
    for lis in entry_points.values():
        for elt in lis:
            list_of_entry_points.append(elt)

    # for each location check if potential entry point then check if in locations (both sides)
    potential_entry_point = None
    new_locations = []
    for location in initial_locations:

        if location['Location'] in list_of_entry_points and potential_entry_point is None:
            for entry_point in entry_points.keys():
                if location['Location'] in entry_points[entry_point]:
                    potential_entry_point = entry_point

        # check l keys
        if location['Location'] in locations_map:
            location['location'] = locations_map[location.pop('Location')][0]
            new_locations.append(location)
            continue

        # check l values
        for location_name in locations_map.keys():
            if location['Location'] in locations_map[location_name]:
                location['location'] = locations_map[location_name][0]
                location.pop('Location')
                new_locations.append(location)
                continue

    return [new_locations, potential_entry_point]


def parse_charlwood_train(sim_id: str, train_cat, **kwargs):
    if 'train_id' in kwargs:
        train_file_as_string = ''

        # f = open(f'charlwoodhouse.co.uk/rail/liverail/train/{kwargs['train_id']}/14/02/20.html', "r")
        f = open('assorted_files/charlwoodhousesimsig/t20.html', "r")
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

    # Work out other fields for train from train cat dict
    train_info = complete_train_info(sim_id, train_info)

    # Filter locations out via sim locations and translate TIPLOC to readable
    [readable_locations, potential_entry_point] = convert_train_locations(sim_id, initial_locations)

    # Send locations in to sim specific location logic, **this will give entry point and time if applic.**


    for l in readable_locations:
        print(l)
    print(potential_entry_point)
    print(header_data)
    print(train_info)

parse_charlwood_train('newport', None, train_link='http://www.charlwoodhouse.co.uk/rail/liverail/train/22398631/31/03/21' )

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
            if len(fields) > 0:
                formatted_times_field = fields[1].get_text().replace('&half', '.5').replace('\n', '')
                time_match_obj = re.match('.*(\\d{2}:\\d{2}(?:\\.5)?)', formatted_times_field)
                list_of_times.append(
                    [float(time_match_obj.group(1).replace(':', '')), fields[2].find('a')['href']])

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

    return [x[1] for x in list_of_times]


def parse_charlwood_house_location_file(start_time: str, end_time: str, location_of_file: str) -> list:
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
        summary_page = BeautifulSoup(location_page_as_string, 'html.parser')
        list_of_links = parse_summary_page(start_time, end_time, summary_page)

        return [re.match('.*/train/(\\d+)/.*', x).group(1) for x in list_of_links]

    elif '/full/' in location_of_file:
        full_page = BeautifulSoup(location_page_as_string, 'html.parser')
        list_of_links = parse_full_page(start_time, end_time, full_page)

        return [re.match('.*/train/(\\d+)/.*', x).group(1) for x in list_of_links]
    else:
        print('Could not determine location file type: ' + location_of_file)
        return []


def parse_charlwood_house_location_page(start_time: str, end_time: str, location_page_link: str) -> list:
    """
    :param start_time: start of period to look for trains in format hhmm
    :param end_time: end of period to look for trains in format hhmm
    :param location_page_link: relative path to charlwoodhouse locations page.
    :return: list of links to charlwoodhouse train pages.
    """

    response = requests.get(location_page_link)

    if '/sum/' in location_page_link:
        summary_page = BeautifulSoup(response.content, 'html.parser')
        list_of_links = parse_summary_page(start_time, end_time, summary_page)

        return [f'http://charlwoodhouse.co.uk{x}' for x in list_of_links]

    elif '/full/' in location_page_link:
        full_page = BeautifulSoup(response.content, 'html.parser')
        list_of_links = parse_full_page(start_time, end_time, full_page)

        return [f'http://charlwoodhouse.co.uk{x}' for x in list_of_links]
    else:
        print('Could not determine location page type: ' + location_page_link)
        return []


def parse_rtt_location_page():
    return None


# print(parse_charlwood_house_location_page('0400', '2400', 'http://charlwoodhouse.co.uk/rail/liverail/full/sdon/26/03/20'))
