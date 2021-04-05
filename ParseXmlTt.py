import xml.etree.ElementTree as ET
import zipfile
from dbClient import *
import common

DEFAULT_CATEGORY = {'id': 'A0000001', 'accel_brake_index': '1',
                    'is_freight': '-1', 'can_use_goods_lines': '-1', 'max_speed': '60', 'train_length': '300',
                    'speed_class': '512', 'power_to_weight_category': '0',
                    'dwell_times': {'join': '240', 'divide': '240', 'crew_change': '120'}, 'electrification': 'D'}


def parse_xml_trips(list_of_trip_elts, tiploc_dict: dict, first_loc_is_stop: bool) -> list:
    ACT_DICT = {'0': 'trainBecomes', '1': 'divideRear', '2': 'divideFront', '3': 'trainJoins', '4': 'detachRear',
                '5': 'detachFront', '6': 'dropRear', '7': 'dropFront', '8': 'joins2', '9': 'platformShare',
                '10': 'crewChange'}
    out = []
    for trip in list_of_trip_elts:
        location = {}
        location['location'] = tiploc_dict[trip.find('Location').text][0]
        if trip.find('DepPassTime') is not None:
            location['dep'] = common.convert_sec_to_time(int(trip.find('DepPassTime').text))
            if trip.find('ArrTime') is None and first_loc_is_stop is True:
                first_loc_is_stop = False
                location['isOrigin'] = 'yes'
        if trip.find('ArrTime') is not None:
            location['arr'] = common.convert_sec_to_time(int(trip.find('ArrTime').text))
        if trip.find('Platform') is not None:
            location['plat'] = trip.find('Platform').text
        if trip.find('Line') is not None:
            location['line'] = trip.find('Line').text
        if trip.find('Path') is not None:
            location['path'] = trip.find('Path').text
        if trip.find('PathAllowance') is not None:
            location['pth allow'] = trip.find('PathAllowance').text
        if trip.find('EngAllowance') is not None:
            location['eng allow'] = trip.find('EngAllowance').text

        if trip.find('Activities') is not None:
            location['activities'] = {}
            for activity in trip.find('Activities').findall('Activity'):
                if activity.find('AssociatedUID') is not None:
                    location['activities'][ACT_DICT[activity.find('Activity').text]] = activity.find('AssociatedUID').text
                else:
                    location['activities'][ACT_DICT[activity.find('Activity').text]] = None

        out.append(location)
    return out


def parse_individual_xml_tt(xml_tt: ET.Element, tiploc_dict: dict, categories_dict: dict) -> dict:
    json_tt = {}
    first_loc_is_stop = False
    if xml_tt.find('EntryPoint') is None:
        if xml_tt.find('SeedPoint') is None:
            json_tt['tt_template'] = 'templates/timetables/defaultTimetableNoEP.txt'
            first_loc_is_stop = True
        else:
            json_tt['tt_template'] = 'templates/timetables/defaultTimetableSeedPoint.txt'
    else:
        json_tt['tt_template'] = 'templates/timetables/defaultTimetableWithEntryPoint.txt'

    if xml_tt.find('Category') is not None:
        cat_id = xml_tt.find('Category').text
    else:
        # Use default i
        cat_id = 'A0000001'

    json_tt['category'] = categories_dict[cat_id]['description']
    json_tt['uid'] = xml_tt.find('UID').text
    json_tt['headcode'] = xml_tt.find('ID').text
    json_tt['max_speed'] = xml_tt.find('MaxSpeed').text
    json_tt['train_length'] = xml_tt.find('TrainLength').text
    json_tt['electrification'] = xml_tt.find('Electrification').text
    json_tt['description'] = xml_tt.find('Description').text
    json_tt['start_traction'] = xml_tt.find('StartTraction').text

    if xml_tt.find('AccelBrakeIndex') is not None:
        json_tt['accel_brake_index'] = xml_tt.find('AccelBrakeIndex').text
    else:
        json_tt['accel_brake_index'] = categories_dict[cat_id]['accel_brake_index']

    if xml_tt.find('IsFreight') is not None:
        json_tt['is_freight'] = xml_tt.find('IsFreight').text
    else:
        json_tt['is_freight'] = categories_dict[cat_id]['is_freight']

    if xml_tt.find('CanUseGoodsLines') is not None:
        json_tt['can_use_goods_lines'] = xml_tt.find('CanUseGoodsLines').text
    elif 'can_use_goods_lines' in categories_dict[cat_id]:
        json_tt['can_use_goods_lines'] = categories_dict[cat_id]['can_use_goods_lines']

    if xml_tt.find('OriginName') is not None:
        json_tt['origin_name'] = xml_tt.find('OriginName').text
    else:
        json_tt['origin_name'] = 'Default'

    if xml_tt.find('DestinationName') is not None:
        json_tt['destination_name'] = xml_tt.find('DestinationName').text
    else:
        json_tt['destination_name'] = 'Default'

    if xml_tt.find('OriginTime') is not None:
        json_tt['origin_time'] = common.convert_sec_to_time(int(xml_tt.find('OriginTime').text))
    else:
        json_tt['origin_time'] = '0000'

    if xml_tt.find('DestinationTime') is not None:
        json_tt['destination_time'] = common.convert_sec_to_time(int(xml_tt.find('DestinationTime').text))
    else:
        json_tt['destination_time'] = '0000'

    if xml_tt.find('OperatorCode') is not None:
        json_tt['operator_code'] = xml_tt.find('OperatorCode').text
    else:
        json_tt['operator_code'] = 'ZZ'

    if xml_tt.find('SpeedClass') is not None:
        json_tt['speed_class'] = xml_tt.find('SpeedClass').text
    else:
        json_tt['speed_class'] = categories_dict[cat_id]['speed_class']

    # Some actually optional stuff
    if xml_tt.find('EntryPoint') is not None:
        json_tt['entry_point'] = xml_tt.find('EntryPoint').text
    if xml_tt.find('SeedPoint') is not None:
        json_tt['seed_point'] = xml_tt.find('SeedPoint').text
    if xml_tt.find('DepartTime') is not None:
        json_tt['entry_time'] = common.convert_sec_to_time(int(xml_tt.find('DepartTime').text))

    if xml_tt.find('Join') is not None:
        json_tt['dwell_times'] = {}
        json_tt['dwell_times']['join'] = xml_tt.find('Join').text
        json_tt['dwell_times']['divide'] = xml_tt.find('Divide').text
        json_tt['dwell_times']['crew_change'] = xml_tt.find('CrewChange').text

    json_tt['locations'] = parse_xml_trips(xml_tt.find('Trips').findall('Trip'), tiploc_dict, first_loc_is_stop)
    print('Parsed ' + json_tt['headcode'])
    return json_tt


def parse_individual_xml_rule(rule: ET.Element) -> dict:
    RULE_NAMES_DICT = {'0': 'XAppAfterYEnt', '1': 'XAppAfterYLve', '2': 'XAppAfterYArr', '3': 'XNotIfY',
                       '4': 'XDepAfterYArr',
                       '5': 'XDepAfterYEnt', '6': 'XDepAfterYLve', '7': 'XDepAfterYJoin', '8': 'XDepAfterYDiv',
                       '9': 'XDepAfterYForm', '10': 'XYMutExc', '11': 'XAppAfterYJoin', '12': 'XAppAfterYDiv',
                       '13': 'XAppAfterYForm', '14': 'XYAlternatives'}
    json_rule = {'name': RULE_NAMES_DICT[rule.find('Rule').text],
                 'train_x': rule.find('TrainUID').text,
                 'train_y': rule.find('Train2UID').text}

    if rule.find('Time') is not None:
        json_rule['time'] = rule.find('Time').text

    if rule.find('Location') is not None:
        json_rule['location'] = rule.find('Location').text

    return json_rule


def validate_categories(cat_root):
    list_of_descriptions = []
    descriptions_with_ids = {}
    errors = []
    for category in cat_root.findall('TrainCategory'):
        description = category.find('Description').text

        if description not in list_of_descriptions:
            descriptions_with_ids[description] = category.attrib['ID']
            list_of_descriptions.append(description)
        else:
            errors.append(f'{description} used for multiple IDs {category.attrib["ID"]}, {descriptions_with_ids[description]}')

    if len(errors) > 0:
        raise Exception(' '.join(errors))




def parse_train_categories_to_map(xml_tt_root) -> dict:
    """
    Will take an xml excerpt just containing the TrainCategories root from a Simsig TT and give a map of categories
    with the Description as the key. This relies on the descriptions being unique.

    :param xml_tt_root: Element tree.
    :return: A map/python dict of categories with the Description as the key.
    """

    if 'TrainCategories' in xml_tt_root.tag:
        cat_root = xml_tt_root
    else:
        cat_root = xml_tt_root.find('TrainCategories')

    validate_categories(cat_root)

    categories_dict = {'standard diesel freight': DEFAULT_CATEGORY}
    for category in cat_root.findall('TrainCategory'):
        description = category.find('Description').text
        categories_dict[description] = {'id': category.attrib['ID']}
        if category.find('AccelBrakeIndex') is not None:
            categories_dict[description]['accel_brake_index'] = category.find('AccelBrakeIndex').text
        if category.find('IsFreight') is not None:
            categories_dict[description]['is_freight'] = category.find('IsFreight').text
        if category.find('CanUseGoodsLines') is not None:
            categories_dict[description]['can_use_goods_lines'] = category.find('CanUseGoodsLines').text
        if category.find('MaxSpeed') is not None:
            categories_dict[description]['max_speed'] = category.find('MaxSpeed').text
        if category.find('TrainLength') is not None:
            categories_dict[description]['train_length'] = category.find('TrainLength').text
        if category.find('SpeedClass') is not None:
            categories_dict[description]['speed_class'] = category.find('SpeedClass').text
        if category.find('PowerToWeightCategory') is not None:
            categories_dict[description]['power_to_weight_category'] = category.find('PowerToWeightCategory').text
        if category.find('Electrification') is not None:
            categories_dict[description]['electrification'] = category.find('Electrification').text
        if category.find('DwellTimes') is not None:
            dwell_times = category.find('DwellTimes')
            dwell_times_dict = {}
            if dwell_times.find('Join') is not None:
                dwell_times_dict['join'] = dwell_times.find('Join').text
            if dwell_times.find('Divide') is not None:
                dwell_times_dict['divide'] = dwell_times.find('Divide').text
            if dwell_times.find('CrewChange') is not None:
                dwell_times_dict['crew_change'] = dwell_times.find('CrewChange').text

            if len(dwell_times_dict) > 0:
                categories_dict[description]['dwell_times'] = dwell_times_dict

    return categories_dict


def Parse_Full_Xml_Tt(file: str, overwrite_existing: bool):
    with zipfile.ZipFile(file, 'r') as zip_ref:
        zip_ref.extractall('temp_parsing_dir')

    tree = ET.parse('temp_parsing_dir/SavedTimetable.xml')

    os.remove('temp_parsing_dir/SavedTimetable.xml')
    os.remove('temp_parsing_dir/TimetableHeader.xml')
    os.rmdir('temp_parsing_dir')

    root = tree.getroot()
    tt_header = {'sim_id': root.attrib['ID'],
                 'version': root.attrib['Version'],
                 'name': root.find('Name').text.replace(' ', '_'),
                 'actual_name': root.find('Name').text,
                 'description': root.find('Description').text,
                 'start_time': common.convert_sec_to_time(int(root.find('StartTime').text)),
                 'finish_time': common.convert_sec_to_time(int(root.find('FinishTime').text)),
                 'v_major': root.find('VMajor').text,
                 'v_minor': root.find('VMinor').text,
                 'v_build': root.find('VBuild').text,
                 'train_description_template': root.find('Description').text}
    locations_map = common.create_location_map_from_file(tt_header['sim_id'])[1]

    tt_db = TrainTtDb(tt_header['name'])
    rules_db = RulesDb(tt_header['name'])
    header_db = MainHeaderDb(tt_header['name'])

    header_db.add_header(tt_header)

    categories_map = parse_train_categories_to_map(root)
    categories_by_id = common.make_id_key_category_map(categories_map)
    header_db.add_categories_map(categories_map)

    list_of_tt_elts = root.find('Timetables').findall('Timetable')

    for tt in list_of_tt_elts:
        if overwrite_existing is True:
            tt_db.add_tt(parse_individual_xml_tt(tt, locations_map, categories_by_id))
        else:
            tt_db.add_tt_if_not_present(parse_individual_xml_tt(tt, locations_map, categories_by_id))

    if root.find('TimetableRules') is not None:
        list_of_rule_elts = root.find('TimetableRules').findall('TimetableRule')

        for rule in list_of_rule_elts:
            if overwrite_existing is True:
                rules_db.add_rule(parse_individual_xml_rule(rule))
            else:
                rules_db.add_rule_if_not_present(parse_individual_xml_rule(rule))
