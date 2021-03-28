"""
Will be a pretty long file for taking TT data from a list of location sources, fetching all trains within a window,
parsing them and creating Json TTs to put into a DB. This file will pass back a list of Json TTs for parsing.
"""
import requests
from bs4 import BeautifulSoup
import re

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
    :param table: Beautiful Soup version of the sched-table
    :return: list of locations for the train to then tidy up with futher logic.
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
                tiploc = re.match('.*/sum/([A-Z0-9]+)/.*',a_tag['href']).group(1)
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

    :param train_info_table:
    :return: map like: { uid, operator_code, headcode?, Train category?, Power type?, Timing Load?, max_speed?, Train Status? }
    """
    rows_interested_in = ['Train UID', 'ATOC code', 'Signalling ID', 'Train category', 'Power type', 'Timing Load',
                          'Speed', 'Train Status']
    out = {}
    for row in train_info_table.find_all('tr'):

        # want UID 0, ATOC 0 if present, sig ID 0 if present, train cat 0 if present, power type 0 if present, timing load 0 and 1 if present
        # speed 0 if present
        # train status 1 if present
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
                out['Train category'] = row_1 + ' ' + row_2

        if row_name == 'Power type':
            if row_1 not in ['', ' ']:
                out['Power type'] = row_1

        if row_name == 'Timing Load':
            if row_1 not in ['', ' '] or row_2 not in ['', ' ']:
                out['Timing Load'] = row_1 + ' ' + row_2

        if row_name == 'Speed':
            if row_1 not in ['', ' ']:
                out['max_speed'] = int(row_1)

        if row_name == 'Train Status':
            if row_1 not in ['', ' ']:
                out['Train Status'] = row_2

    return out


def parse_train_header(header_text: str) -> dict:
    match = re.match('Train (\\d+) \\(.+\\) (?:[0-9][A-Z][0-9]{2})? (\\d{2}:\\d{2}) (.+) to (.+)', header_text)

    return {'ch_id': match.group(1), 'origin_time': match.group(2).replace(':', ''), 'origin_name': match.group(3),
           'dest_name': match.group(4)}



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

    # Sort headcode
    if 'headcode' not in train_info:
        train_info['headcode'] = header_data['ch_id'][:4]

    # Fetch location data from sched table
    initial_locations = parse_sched_table(train_page.find('table', {'class': 'sched-table'}))

    # Work out other fields for train from train cat dict

    # Filter locations out via sim locations and translate TIPLOC to readable

    # Send locations in to sim specific location logic, **this will give entry point and time if applic.**

    print(initial_locations)
    print(header_data)
    print(train_info)



def parse_charlwood_house_location_file(start_time: str, end_time: str, location_of_file: str) -> list:
    """

    :param start_time:
    :param end_time:
    :param location_of_file: relative path to locations file.
    :return: list of train ids to parse the individual files.
    """
    return None

def parse_charlwood_house_location_page():
    return None


def parse_rtt_location_page():
    return None

parse_charlwood_train('', '', train_link='http://charlwoodhouse.co.uk/rail/liverail/train/23598269/28/03/21')