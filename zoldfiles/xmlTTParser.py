import xml.etree.ElementTree as ET
from translateTimesAndLocations import convert_sec_to_time
from dbClient import *
from tiplocDictCreator import create_tiploc_dict, pull_train_categories_out_of_xml_file_by_id


def parse_xml_trips(list_of_trip_elts, tiploc_dict: dict, first_loc_is_stop: bool) -> list:
    ACT_DICT = {'0': 'trainBecomes', '1': 'divideRear', '2': 'divideFront', '3': 'trainJoins', '4': 'detachRear',
                '5': 'detachFront', '6': 'dropRear', '7': 'dropFront', '8': 'joins2', '9': 'platformShare',
                '10': 'crewChange'}
    out = []
    for trip in list_of_trip_elts:
        location = {}
        location['location'] = tiploc_dict[trip.find('Location').text][0]
        if trip.find('DepPassTime') is not None:
            location['dep'] = convert_sec_to_time(int(trip.find('DepPassTime').text))
            if trip.find('ArrTime') is None and first_loc_is_stop is True:
                first_loc_is_stop = False
                location['isOrigin'] = 'yes'
        if trip.find('ArrTime') is not None:
            location['arr'] = convert_sec_to_time(int(trip.find('ArrTime').text))
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

    cat_id = xml_tt.find('Category').text
    json_tt['category'] = categories_dict[cat_id]['Description']
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
        json_tt['accel_brake_index'] = categories_dict[cat_id]['AccelBrakeIndex']
    if xml_tt.find('IsFreight') is not None:
        json_tt['is_freight'] = xml_tt.find('IsFreight').text
    else:
        json_tt['is_freight'] = categories_dict[cat_id]['IsFreight']
    if xml_tt.find('OriginName') is not None:
        json_tt['origin_name'] = xml_tt.find('OriginName').text
    else:
        json_tt['origin_name'] = 'Default'
    if xml_tt.find('DestinationName') is not None:
        json_tt['destination_name'] = xml_tt.find('DestinationName').text
    else:
        json_tt['destination_name'] = 'Default'
    if xml_tt.find('OriginTime') is not None:
        json_tt['origin_time'] = convert_sec_to_time(int(xml_tt.find('OriginTime').text))
    else:
        json_tt['origin_time'] = '0000'
    if xml_tt.find('DestinationTime') is not None:
        json_tt['destination_time'] = convert_sec_to_time(int(xml_tt.find('DestinationTime').text))
    else:
        json_tt['destination_time'] = '0000'
    if xml_tt.find('OperatorCode') is not None:
        json_tt['operator_code'] = xml_tt.find('OperatorCode').text
    else:
        json_tt['operator_code'] = 'ZZ'
    if xml_tt.find('SpeedClass') is not None:
        json_tt['speed_class'] = xml_tt.find('SpeedClass').text
    else:
        json_tt['speed_class'] = categories_dict[cat_id]['SpeedClass']

    # Some actually optional stuff
    if xml_tt.find('EntryPoint') is not None:
        json_tt['entry_point'] = xml_tt.find('EntryPoint').text
    if xml_tt.find('SeedPoint') is not None:
        json_tt['seed_point'] = xml_tt.find('SeedPoint').text
    if xml_tt.find('DepartTime') is not None:
        json_tt['entry_time'] = convert_sec_to_time(int(xml_tt.find('DepartTime').text))

    if xml_tt.find('Join') is not None:
        json_tt['dwell_times'] = {}
        json_tt['dwell_times']['join'] = xml_tt.find('Join').text
        json_tt['dwell_times']['divide'] = xml_tt.find('Divide').text
        json_tt['dwell_times']['crew_change'] = xml_tt.find('CrewChange').text

    json_tt['locations'] = parse_xml_trips(xml_tt.find('Trips').findall('Trip'), tiploc_dict, first_loc_is_stop)
    print('Parsed ' + json_tt['headcode'])
    return json_tt


def parse_individual_xml_rule(rule: ET.Element) -> dict:
    RULE_NAMES_DICT = {'0': 'AppAfterEnt', '1': 'AppAfterLve', '2': 'AppAfterArr??', '3': 'NotIf', '4': '???',
                       '5': 'DepAfterEnt', '6': 'DepAfterLve', '7': 'DepAfterJoin', '8': 'DepAfterDiv',
                       '9': 'DepAfterForm', '10': '	MutExc', '11': 'AppAfterJoin', '12': '	AppAfterDiv',
                       '13': 'AppAfterForm', '14': 'Alternatives'}
    json_rule = {'name': RULE_NAMES_DICT[rule.find('Rule').text],
                 'train_x': rule.find('TrainUID').text,
                 'train_y': rule.find('Train2UID').text}

    if rule.find('Time') is not None:
        json_rule['time'] = rule.find('Time').text

    if rule.find('Location') is not None:
        json_rule['location'] = rule.find('Location').text

    return json_rule


def get_categories_as_string(file: str) -> str:
    f = open(file, mode='r')
    train_cats = False
    train_cat_string = ''
    for fl in f:
        if '<TrainCategories>' in fl:
            train_cat_string += fl.rstrip()
            train_cats = True
            continue
        if '</TrainCategories>' in fl:
            train_cat_string += fl.rstrip()
            train_cats = False
            continue
        if train_cats is True:
            train_cat_string += fl.rstrip()

    return train_cat_string


def parse_full_xml_tt(file: str, locations_file: str, overwrite_existing: bool):
    tree = ET.parse(file)
    root = tree.getroot()
    tiploc_dict = create_tiploc_dict(locations_file)[1]
    tt_header = {'id': root.attrib['ID'],
                 'version': root.attrib['Version'],
                 'name': root.find('Name').text.replace(' ', '_'),
                 'actual_name': root.find('Name').text,
                 'description': root.find('Description').text,
                 'start_time': convert_sec_to_time(int(root.find('StartTime').text)),
                 'finish_time': convert_sec_to_time(int(root.find('FinishTime').text)),
                 'v_major': root.find('VMajor').text,
                 'v_minor': root.find('VMinor').text,
                 'v_build': root.find('VBuild').text,
                 'train_description_template': root.find('Description').text}

    tt_db = TrainTtDb(tt_header['name'])
    rules_db = RulesDb(tt_header['name'])
    header_db = MainHeaderDb(tt_header['name'])

    header_db.add_header(tt_header)
    header_db.add_categories_string(get_categories_as_string(file))

    categories_dict = pull_train_categories_out_of_xml_file_by_id(file)
    list_of_tt_elts = root.find('Timetables').findall('Timetable')

    for tt in list_of_tt_elts:
        if overwrite_existing is True:
            tt_db.add_tt(parse_individual_xml_tt(tt, tiploc_dict, categories_dict))
        else:
            tt_db.add_tt_if_not_present(parse_individual_xml_tt(tt, tiploc_dict, categories_dict))

    if root.find('TimetableRules') is not None:
        list_of_rule_elts = root.find('TimetableRules').findall('TimetableRule')

        for rule in list_of_rule_elts:
            if overwrite_existing is True:
                rules_db.add_rule(parse_individual_xml_rule(rule))
            else:
                rules_db.add_rule_if_not_present(parse_individual_xml_rule(rule))


parse_full_xml_tt('Swindon February 2021/SavedTimetable.xml', '../sim_location_files/swindon_locations.txt', True)
