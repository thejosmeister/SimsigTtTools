"""
A file containing common functions used in multiple files.
"""
import math
import re

import yaml

def create_location_map_from_file(sim_id: str) -> list:
    """
    Takes a yaml file containing a map of location codes to the various names you want these codes to match to.
    e.g: File with maps

    Locations:
    SDONLY: Swindon Loco Yard
    STRUMLC:St. Mary's Level Crossing

    Will become {'locations': {'SDONLY':['Swindon Loco Yard'], 'STRUMLC': ['St. Mary's Level Crossing']}

    :param sim_id: Used to fetch file with locations map in format shown above.
    :return: List of 2 maps, Entry Points and Locations, with location code as the key.
    """

    with open(f'location_maps/{sim_id}.yaml', 'r') as stream:
        location_data = yaml.safe_load(stream)

    entry_points = location_data['entry_points']
    locations = location_data['locations']

    for entry_point in entry_points:
        # parse readable names
        if isinstance(entry_points[entry_point]['readable_names'], str):
            entry_points[entry_point]['readable_names'] = entry_points[entry_point]['readable_names'].split(',')

        if not isinstance(entry_points[entry_point]['readable_names'], list):
            raise Exception(f'Entry point readable names not in acceptable format: {entry_point}')

        entry_points[entry_point]['readable_names'] = [s.strip() for s in entry_points[entry_point]['readable_names']]

    for location in locations:
        if isinstance(locations[location], str):
            locations[location] = locations[location].split(',')

        if not isinstance(locations[location], list):
            raise Exception(f'Location readable names not in acceptable format: {location}')

        locations[location] = [s.strip() for s in locations[location]]

    return [entry_points, locations]


def create_categories_map_from_yaml(categories_yaml_file_name: str) -> dict:
    """
    :param categories_yaml_file_name: yaml file with categories specified
    :return: a parsed instance of the yaml file with some of the criteria stuff refined.
    """
    # TODO incorporate default cat map into any custom one in case?

    with open(f'spec_files/train_categories/{categories_yaml_file_name}', 'r') as stream:
        category_data = yaml.safe_load(stream)

    # make criteria a bit more usable
    for cat in category_data.keys():
        for criteria in category_data[cat]['criteria'].keys():
            parts = category_data[cat]['criteria'][criteria].split('**')
            if len(parts) == 1:
                # just regex
                category_data[cat]['criteria'][criteria] = {'match': parts[0]}
                continue

            # We have some terms before regex
            category_data[cat]['criteria'][criteria] = {'match': parts[-1], 'not': []}
            for term in parts[:-1]:
                if term[0] == '!':
                    category_data[cat]['criteria'][criteria]['not'].append(term[1:])

    return category_data


def find_tiploc_for_location(location_name: str, locations_map: dict) -> str:
    """
    :param location_name: readable version of a location (can also be tiploc).
    :param locations_map: the locations map to find tiploc from.
    :return: the tiploc version if present, if not then empty string.
    """

    for tiploc in locations_map:
        if location_name in locations_map[tiploc]:
            return tiploc

    # could have already passed in tiploc
    if location_name in locations_map:
        return location_name

    return ''


def find_readable_location(location_name: str, locations_map: dict) -> str:
    """
    :param location_name: a readable or tiploc version of a location.
    :param locations_map: the locations map to find readable version from.
    :return: the first readable version if present, if not then empty string.
    """

    # if we pass in tiploc
    if location_name in locations_map:
        return locations_map[location_name][0]

    # if we pass in same or another readable location
    for tiploc in locations_map:
        if location_name in locations_map[tiploc]:
            return locations_map[tiploc][0]

    return ''


def convert_time_to_secs(time: str) -> int:
    """
    Converts a time string in the format hhmm to seconds past midnight
    :param time: Time string, format hhmm
    :return: The time as seconds from midnight
    """
    match = re.match("(\\d{2})(\\d{2})(?:\\.(\\d+))?", time)
    hours = int(match.group(1))
    mins = int(match.group(2))
    if len(time) > 4:
        secs = math.floor(60 * float('0.' + match.group(3)))
    else:
        secs = 0

    return (3600 * hours) + (60 * mins) + secs


def convert_sec_to_time(time: int) -> str:
    """
    Converts seconds past midnight to a time string in the format hhmm.
    :param time: Seconds past midnight
    :return:
    """
    hours = math.floor(time / 3600)
    mins = math.floor((time - (hours * 3600))/60)
    secs = math.floor(time - (hours * 3600) - (mins * 60))

    if secs > 0:
        return f"{hours:02d}{mins:02d}." + str(round(secs/60, 1))[2:3]
    else:
        return f"{hours:02d}{mins:02d}"


def make_id_key_category_map(categories_map: dict) -> dict:
    """
    Makes a map of categories with the key being the id.
    """
    out = {}

    for desc in categories_map:
        id = categories_map[desc]['id']
        out[id] = categories_map[desc].copy()
        out[id]['description'] = desc
        out[id].pop('id')

    return out



# a = {'1':{'id':'x', 'filed': 'y'}, '2':{'id':'z', 'fil': 'sdasa'}}
# print(make_id_key_category_map(a))