import dbClient
import parseData
import yaml
import re
import requests
from bs4 import BeautifulSoup


def fetch_allox_from_page(train_link):
    response = requests.get(train_link)
    train_page = BeautifulSoup(response.content, 'html.parser')
    train_info_panels = train_page.find_all('div', {'class': 'callout infopanel'})
    uid = ''
    allox = ''

    for panel in train_info_panels:
        for line in panel.find_all('li'):
            if line.find('i', class_='glyphicons-database') is not None:
                uid = re.search('UID ([0-9A-Z]+),', line.get_text()).group(1)
            if line.find('div', class_='allocation') is not None:
                allox = parseData.determine_rtt_allocation(line)

    return uid, allox


def AddAlloxToTt(name_of_spec_file: str):
    with open(f'spec_files/add_allox_to_tt_specs/{name_of_spec_file}.yaml', 'r') as stream:
        spec_data = yaml.safe_load(stream)

    # look for TT data
    tt_name = spec_data['tt_name']
    locations = spec_data['locations']
    train_db = dbClient.TrainTtDb(tt_name)

    # Specify locations and times to extract allox from
    list_of_trains = []
    for location_spec in locations:

        location, trains_at_location = parseData.Parse_Rtt_Location_Page(locations[location_spec]['start'],
                                                                         locations[location_spec]['end'], location_spec)
        for train in trains_at_location:
            if 'allox_id' in train:
                list_of_trains.append(train)

    set_of_trains = set(list_of_trains)

    for train in set_of_trains:
        uid, allox = fetch_allox_from_page(train)

        if uid == '' or allox == '':
            continue

        train_tt = train_db.get_tt_by_uid(uid)

        if train_tt is not None:
            print(f'Updating TT for {uid} with allox: {allox}')
            train_tt['description'] = f'{train_tt["origin_time"]} {train_tt["origin_name"]} - {train_tt["destination_name"]} {train_tt["operator_code"]} ({allox})'
            train_db.put_tt_by_uid(uid, train_tt)


