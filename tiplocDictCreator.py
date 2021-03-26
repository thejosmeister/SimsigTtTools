"""
Some utils for extracting stuff from xml files
"""
import xml.etree.ElementTree as ET


def pull_tiploc_out_of_xml(files_to_pull_tiploc_out: list, out_filename):
    """
    Will fetch any location codes within Simsig TTs for the same sim and output a list to a text file.
    Separates the entry locations from others.
    I used it to create a dictionary of locations in a sim where there is not one provided in the documentation.

    :param files_to_pull_tiploc_out: The Simsig TT.
    :param out_filename: Name of ouput file.
    """
    entry_points = []
    locations = []
    for file_to_pull_tiploc_out in files_to_pull_tiploc_out:
        f = open(file_to_pull_tiploc_out, "r")
        for file_line in f:
            if '<EntryPoint>' in file_line:
                entry_points.append(file_line.split('<EntryPoint>')[1].split('</EntryPoint>')[0])
            if '<Location>' in file_line:
                locations.append(file_line.split('<Location>')[1].split('</Location>')[0])

        f.close()

    set_of_entry_points = set(entry_points)
    set_of_locations = set(locations)

    with open(out_filename, mode='w') as emails_file:
        print('Entry Points: ', file=emails_file)
        for e in set_of_entry_points:
            print(e, file=emails_file)
        print(' ', file=emails_file)
        print('Locations: ', file=emails_file)
        for e in set_of_locations:
            print(e, file=emails_file)


pull_tiploc_out_of_xml(['future_planning/Newport SO 21 11 2015 0000 Start/SavedTimetable.xml',
                        'future_planning/Newport SX 08 04 2015 0000 Start/SavedTimetable.xml',
                        'future_planning/Newport  FEB 2020 PLUS/SavedTimetable.xml'],
                       'sim_location_files/newport_locations.txt')

def pull_train_categories_out_of_xml_string(categories_string: str) -> dict:
    root = ET.fromstring(categories_string)
    return pull_train_categories_out_of_xml(root)


def pull_train_categories_out_of_xml_file(file_with_categories: str) -> dict:
    tree = ET.parse(file_with_categories)
    root = tree.getroot()
    return pull_train_categories_out_of_xml(root)


def pull_train_categories_out_of_xml(root) -> dict:
    """
    Will take an xml excerpt just containing the TrainCategories root from a Simsig TT and give a map of categories
    with the Description as the key. This relies on the descriptions being unique.

    :param root: Element tree.
    :return: A map/python dict of categories with the Description as the key.
    """

    if 'TrainCategories' in root.tag:
        cat_root = root
    else:
        cat_root = root.find('TrainCategories')

    categories_dict = {}
    for category in cat_root.findall('TrainCategory'):
        description = category.find('Description').text
        categories_dict[description] = {'id': category.attrib['ID']}
        if category.find('AccelBrakeIndex') is not None:
            categories_dict[description]['AccelBrakeIndex'] = category.find('AccelBrakeIndex').text
        if category.find('IsFreight') is not None:
            categories_dict[description]['IsFreight'] = category.find('IsFreight').text
        if category.find('CanUseGoodsLines') is not None:
            categories_dict[description]['CanUseGoodsLines'] = category.find('CanUseGoodsLines').text
        if category.find('MaxSpeed') is not None:
            categories_dict[description]['MaxSpeed'] = category.find('MaxSpeed').text
        if category.find('TrainLength') is not None:
            categories_dict[description]['TrainLength'] = category.find('TrainLength').text
        if category.find('SpeedClass') is not None:
            categories_dict[description]['SpeedClass'] = category.find('SpeedClass').text
        if category.find('PowerToWeightCategory') is not None:
            categories_dict[description]['PowerToWeightCategory'] = category.find('PowerToWeightCategory').text
        if category.find('Electrification') is not None:
            categories_dict[description]['Electrification'] = category.find('Electrification').text
        if category.find('DwellTimes') is not None:
            dwell_times = category.find('DwellTimes')
            dwell_times_dict = {}
            if dwell_times.find('Join') is not None:
                dwell_times_dict['Join'] = dwell_times.find('Join').text
            if dwell_times.find('Divide') is not None:
                dwell_times_dict['Divide'] = dwell_times.find('Divide').text
            if dwell_times.find('CrewChange') is not None:
                dwell_times_dict['CrewChange'] = dwell_times.find('CrewChange').text

            if len(dwell_times_dict) > 0:
                categories_dict[description]['DwellTimes'] = dwell_times_dict

    return categories_dict


def pull_train_categories_out_of_xml_string_by_id(categories_string: str) -> dict:
    root = ET.fromstring(categories_string)
    return pull_train_categories_out_of_xml_by_id(root)


def pull_train_categories_out_of_xml_file_by_id(file_with_categories: str) -> dict:
    tree = ET.parse(file_with_categories)
    root = tree.getroot()
    return pull_train_categories_out_of_xml_by_id(root)


def pull_train_categories_out_of_xml_by_id(root) -> dict:
    """
    Will take an xml excerpt just containing the TrainCategories root from a Simsig TT and give a map of categories
    with the ID as the key.

    :param root: Element tree.
    :return: A map/python dict of categories with the ID as the key.
    """
    if 'TrainCategories' in root.tag:
        cat_root = root
    else:
        cat_root = root.find('TrainCategories')

    categories_dict = {}
    for category in cat_root.findall('TrainCategory'):
        _id = category.attrib['ID']
        categories_dict[_id] = {'Description': category.find('Description').text}
        if category.find('AccelBrakeIndex') is not None:
            categories_dict[_id]['AccelBrakeIndex'] = category.find('AccelBrakeIndex').text
        if category.find('IsFreight') is not None:
            categories_dict[_id]['IsFreight'] = category.find('IsFreight').text
        if category.find('CanUseGoodsLines') is not None:
            categories_dict[_id]['CanUseGoodsLines'] = category.find('CanUseGoodsLines').text
        if category.find('MaxSpeed') is not None:
            categories_dict[_id]['MaxSpeed'] = category.find('MaxSpeed').text
        if category.find('TrainLength') is not None:
            categories_dict[_id]['TrainLength'] = category.find('TrainLength').text
        if category.find('SpeedClass') is not None:
            categories_dict[_id]['SpeedClass'] = category.find('SpeedClass').text
        if category.find('PowerToWeightCategory') is not None:
            categories_dict[_id]['PowerToWeightCategory'] = category.find('PowerToWeightCategory').text
        if category.find('Electrification') is not None:
            categories_dict[_id]['Electrification'] = category.find('Electrification').text
        if category.find('DwellTimes') is not None:
            dwell_times = category.find('DwellTimes')
            dwell_times_dict = {}
            if dwell_times.find('Join') is not None:
                dwell_times_dict['Join'] = dwell_times.find('Join').text
            if dwell_times.find('Divide') is not None:
                dwell_times_dict['Divide'] = dwell_times.find('Divide').text
            if dwell_times.find('CrewChange') is not None:
                dwell_times_dict['CrewChange'] = dwell_times.find('CrewChange').text

            if len(dwell_times_dict) > 0:
                categories_dict[_id]['DwellTimes'] = dwell_times_dict

    return categories_dict


def create_tiploc_dict(file_location: str) -> list:
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
    f = open(file_location, "r")
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
