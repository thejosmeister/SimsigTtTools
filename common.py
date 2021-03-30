"""
A file containing common functions used in multiple files.
"""

def create_location_map_from_file(sim_id: str) -> list:
    """
    Takes a file containing a map of location codes to the various names you want these codes to match to.
    e.g: File with maps

    Locations:
    SDONLY: Swindon Loco Yard
    STRUMLC:St. Mary's Level Crossing

    Will become {'locations': {'SDONLY':['Swindon Loco Yard'], 'STRUMLC': 'St. Mary's Level Crossing'}

    :param file_location: File with locations map in format shown above.
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