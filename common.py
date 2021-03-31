"""
A file containing common functions used in multiple files.
"""

import yaml

def create_location_map_from_file(sim_id: str) -> list:
    """
    Takes a file containing a map of location codes to the various names you want these codes to match to.
    e.g: File with maps

    Locations:
    SDONLY: Swindon Loco Yard
    STRUMLC:St. Mary's Level Crossing

    Will become {'locations': {'SDONLY':['Swindon Loco Yard'], 'STRUMLC': 'St. Mary's Level Crossing'}

    :param sim_id: Used to fetch file with locations map in format shown above.
    :return: List of 2 maps, Entry Points and Locations, with location code as the key.
    """
    tiploc_locations = {}
    entry_points = {}
    is_entry_points = False
    is_locations = False
    f = open(f'location_maps/{sim_id}.txt', "r")
    for file_line in f:
        if 'Entry Points' in file_line:
            is_entry_points = True
            is_locations = False
            continue
        elif 'Locations' in file_line:
            is_entry_points = False
            is_locations = True
            continue
        elif is_entry_points == True:
            code = file_line.rstrip().split(':')[0]
            names = file_line.rstrip().split(':')[1].split(',')
            entry_points[code] = names
        elif is_locations == True:
            code = file_line.rstrip().split(':')[0]
            names = file_line.rstrip().split(':')[1].split(',')
            tiploc_locations[code] = names

    return [entry_points, tiploc_locations]


def create_categories_map_from_yaml(categories_yaml_location: str) -> dict:
    """
    :param categories_yaml_location: yaml file with categories specified
    :return: a parsed instance of the yaml file with some of the criteria stuff refined.
    """
    # TODO incorporate default cat map into any custom one in case?

    with open(categories_yaml_location, 'r') as stream:
        category_data = yaml.safe_load(stream)

    # make criteria a bit more usable
    for cat in category_data.keys():
        for criteria in category_data[cat]['criteria'].keys():
            parts = category_data[cat]['criteria'][criteria].split('**')
            if len(parts) == 1:
                # just regex
                category_data[cat]['criteria'][criteria] = {'match' : parts[0]}
                continue

            # We have some terms before regex
            category_data[cat]['criteria'][criteria] = {'match': parts[-1], 'not': []}
            for term in parts[:-1]:
                if term[0] == '!':
                    category_data[cat]['criteria'][criteria]['not'].append(term[1:])

    return category_data
