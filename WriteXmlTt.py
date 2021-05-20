"""
Writes XML TT from what is stored in Json TT db.
"""
from dbClient import *
import os
import zipfile
import common
from xml.sax.saxutils import escape


def is_location_in_dict(location: str, tiploc_dict: dict) -> str:
    for t in tiploc_dict.keys():
        if location in tiploc_dict[t]:
            return str(t)
    print(f'no location found in locations map for {location}')
    return location


# Will sub in TIPLOC codes for locations in the sim
def sub_in_tiploc(sorted_locations: list, tiploc_dict: dict) -> list:
    out = []
    for l in sorted_locations:
        location = is_location_in_dict(l['location'], tiploc_dict)
        if location != '':
            l['location'] = location
            out.append(l)
    return out


# Reads in TT template file which will be the bare bones of a TT for an individual train.
def read_in_tt_template(timetable_template_location) -> str:
    f = open(timetable_template_location, "r")
    out = ''
    for fl in f:
        out += fl.rstrip()
    f.close()

    return out


# Adds activities if specified in a trip
def add_xml_location_activities(location: dict) -> str:
    out = '<Activities>'
    for activity in location['activities']:
        f = open('templates/activities/' + activity[0] + 'Template.txt', "r")
        if 'crewChange' in activity[0]:
            for fl in f:
                out += fl.rstrip()
        else:
            if '*' in activity[1]:
                phrase_to_insert = f"<AssociatedUID>{activity[1].replace('*', '')}</AssociatedUID>"
            else:
                phrase_to_insert = f"<AssociatedTrain>{activity[1]}</AssociatedTrain>"
            for fl in f:
                out += fl.rstrip().replace('${Assoc}', phrase_to_insert)
        f.close()

    return out + '</Activities>'


def create_xml_trip(location: dict, train_cat_by_desc: dict) -> str:
    out = '<Trip><Location>' + location['location'] + '</Location>'
    if 'dep' in location:
        out += '<DepPassTime>' + str(common.convert_time_to_secs(location['dep'])) + '</DepPassTime>'
    if 'arr' in location:
        out += '<ArrTime>' + str(common.convert_time_to_secs(location['arr'])) + '</ArrTime>'
    if 'is_pass_time' in location:
        out += '<IsPassTime>-1</IsPassTime>'
    if 'plat' in location:
        out += '<Platform>' + location['plat'] + '</Platform>'
    if 'line' in location:
        out += '<Line>' + location['line'] + '</Line>'
    if 'path' in location:
        out += '<Path>' + location['path'] + '</Path>'
    if 'pth allow' in location:
        out += '<PathAllowance>' + location['pth allow'] + '</PathAllowance>'
    if 'eng allow' in location:
        out += '<EngAllowance>' + location['eng allow'] + '</EngAllowance>'
    if 'berths_here' in location:
        out += '<BerthsHere>' + location['berths_here'] + '</BerthsHere>'
    if 'set_down_only' in location:
        out += '<SetDownOnly>' + location['set_down_only'] + '</SetDownOnly>'
    if 'allow_stops_on_through' in location:
        out += '<AllowStopsOnThroughLines>' + location['allow_stops_on_through'] + '</AllowStopsOnThroughLines>'
    if 'stop_location' in location:
        out += '<StopLocation>' + location['stop_location'] + '</StopLocation>'
    if 'stop_adjustment' in location:
        out += '<StopAdjustment>' + location['stop_adjustment'] + '</StopAdjustment>'
    if 'wait_for_booked_time' in location:
        out += '<WaitForBookedTime>' + location['wait_for_booked_time'] + '</WaitForBookedTime>'
    if 'request_percent' in location:
        out += '<RequestPercent>' + location['request_percent'] + '</RequestPercent>'
    if 'dwell_time' in location:
        out += '<DwellTime>' + location['dwell_time'] + '</DwellTime>'
    if 'new_category' in location:
        new_cat = location['new_category']
        if new_cat in train_cat_by_desc:
            new_cat = train_cat_by_desc[new_cat]['id']
        out += '<NewCategory>' + new_cat + '</NewCategory>'

    # Add activities
    if 'activities' in location:
        out += add_xml_location_activities(location)

    return out + '</Trip>'


def convert_individual_json_tt_to_xml(json_tt: dict, locations_map: dict, train_cat_by_id: dict,
                                      train_cat_by_desc: dict, use_default_category: bool) -> str:
    """
    Takes a json timetable for a train and produces an xml one for insertion into a Simsig xml TT.
    :param json_tt: json timetable for a train.
    :param locations_map: map of sim locations.
    :param train_cat_by_id:
    :param train_cat_by_desc:
    :param use_default_category: if train has default category then denotes whether we write with cat or not
    :return: XML string with TT.
    """

    tt_template = read_in_tt_template(json_tt['tt_template'])
    locations_on_sim = sub_in_tiploc(json_tt['locations'], locations_map)
    trips = ''.join([create_xml_trip(l, train_cat_by_desc) for l in locations_on_sim])

    # Sort all the parameters to plug in to template.
    headcode = f"<ID>{json_tt['headcode']}</ID>"

    extras = ''
    category_as_dict = None

    if 'category' in json_tt:
        if 'standard diesel freight' == json_tt['category'] and use_default_category is True:
            # Train has default category
            category = f"<Category>{train_cat_by_desc[json_tt['category']]['id']}</Category>"
        elif 'A0000001' == json_tt['category'] and use_default_category is True:
            # Train has default category
            category = f"<Category>{json_tt['category']}</Category>"
        elif json_tt['category'] in train_cat_by_desc:
            category = f"<Category>{train_cat_by_desc[json_tt['category']]['id']}</Category>"
            category_as_dict = train_cat_by_desc[json_tt['category']]
        else:
            category = f"<Category>{train_cat_by_desc[json_tt['category']]['id']}</Category>"
    else:
        category = ''

    if 'accel_brake_index' in json_tt:
        accel_brake_index = f"<AccelBrakeIndex>{json_tt['accel_brake_index']}</AccelBrakeIndex>"
    elif category_as_dict is not None and 'accel_brake_index' in category_as_dict:
        accel_brake_index = f"<AccelBrakeIndex>{category_as_dict['accel_brake_index']}</AccelBrakeIndex>"
    else:
        accel_brake_index = ''

    if 'uid' in json_tt:
        uid = f"<UID>{json_tt['uid']}</UID>"
    else:
        uid = ''

    if 'max_speed' in json_tt:
        max_speed = f"<MaxSpeed>{json_tt['max_speed']}</MaxSpeed>"
    elif category_as_dict is not None and 'accel_brake_index' in category_as_dict:
        max_speed = f"<MaxSpeed>{category_as_dict['max_speed']}</MaxSpeed>"
    else:
        max_speed = ''

    if 'is_freight' in json_tt:
        is_freight = f"<IsFreight>{json_tt['is_freight']}</IsFreight>"
    elif category_as_dict is not None and 'is_freight' in category_as_dict:
        is_freight = f"<IsFreight>{category_as_dict['is_freight']}</IsFreight>"
    else:
        is_freight = ''

    if 'can_use_goods_lines' in json_tt:
        extras += f"<CanUseGoodsLines>{json_tt['can_use_goods_lines']}</CanUseGoodsLines>"
    elif category_as_dict is not None and 'can_use_goods_lines' in category_as_dict:
        extras += f"<CanUseGoodsLines>{category_as_dict['can_use_goods_lines']}</CanUseGoodsLines>"

    if 'power_to_weight_category' in json_tt:
        extras += f"<PowerToWeightCategory>{json_tt['power_to_weight_category']}</PowerToWeightCategory>"
    elif category_as_dict is not None and 'power_to_weight_category' in category_as_dict:
        extras += f"<PowerToWeightCategory>{category_as_dict['power_to_weight_category']}</PowerToWeightCategory>"

    if 'train_length' in json_tt:
        train_length = f"<TrainLength>{json_tt['train_length']}</TrainLength>"
    elif category_as_dict is not None and 'train_length' in category_as_dict:
        train_length = f"<TrainLength>{category_as_dict['train_length']}</TrainLength>"
    else:
        train_length = ''

    if 'electrification' in json_tt:
        electrification = f"<Electrification>{json_tt['electrification']}</Electrification>"
    elif category_as_dict is not None and 'electrification' in category_as_dict:
        electrification = f"<Electrification>{category_as_dict['electrification']}</Electrification>"
    else:
        electrification = ''

    if 'speed_class' in json_tt:
        speed_class = f"<SpeedClass>{json_tt['speed_class']}</SpeedClass>"
    elif category_as_dict is not None and 'speed_class' in category_as_dict:
        speed_class = f"<SpeedClass>{category_as_dict['speed_class']}</SpeedClass>"
    else:
        speed_class = ''

    if 'origin_name' in json_tt:
        origin_name = f"<OriginName>{escape(json_tt['origin_name'])}</OriginName>"
    else:
        origin_name = ''
    if 'destination_name' in json_tt:
        destination_name = f"<DestinationName>{escape(json_tt['destination_name'])}</DestinationName>"
    else:
        destination_name = ''
    if 'origin_time' in json_tt:
        origin_time = f"<OriginTime>{str(common.convert_time_to_secs(json_tt['origin_time']))}</OriginTime>"
    else:
        origin_time = ''
    if 'destination_time' in json_tt:
        destination_time = f"<DestinationTime>{str(common.convert_time_to_secs(json_tt['destination_time']))}</DestinationTime>"
    else:
        destination_time = ''
    if 'description' in json_tt:
        description = f"<Description>{escape(json_tt['description'])}</Description>"
    else:
        description = ''
    if 'operator_code' in json_tt:
        operator_code = f"<OperatorCode>{json_tt['operator_code']}</OperatorCode>"
    else:
        operator_code = ''
    if 'start_traction' in json_tt:
        start_traction = f"<StartTraction>{json_tt['start_traction']}</StartTraction>"
    else:
        start_traction = ''
    if 'seeding_gap' in json_tt:
        seeding_gap = f"<SeedingGap>{json_tt['seeding_gap']}</SeedingGap>"
    else:
        seeding_gap = ''
    if 'as_required_percent' in json_tt:
        as_required_percent = f"<AsRequiredPercent>{json_tt['as_required_percent']}</AsRequiredPercent>"
    else:
        as_required_percent = ''

    if 'notes' in json_tt:
        extras += f'<Notes>{json_tt["notes"]}</Notes>'

    if 'dwell_times' in json_tt:
        dwell_times = ''
        for dt in json_tt['dwell_times']:
            if 'red_signal_move_off' in dt:
                dwell_times += f"<RedSignalMoveOff>{json_tt['dwell_times']['red_signal_move_off']}</RedSignalMoveOff>"
            if 'station_forward' in dt:
                dwell_times += f"<StationForward>{json_tt['dwell_times']['station_forward']}</StationForward>"
            if 'station_reverse' in dt:
                dwell_times += f"<StationReverse>{json_tt['dwell_times']['station_reverse']}</StationReverse>"
            if 'terminate_forward' in dt:
                dwell_times += f"<TerminateForward>{json_tt['dwell_times']['terminate_forward']}</TerminateForward>"
            if 'terminate_reverse' in dt:
                dwell_times += f"<TerminateReverse>{json_tt['dwell_times']['terminate_reverse']}</TerminateReverse>"
            if 'join' in dt:
                dwell_times += f"<Join>{json_tt['dwell_times']['join']}</Join>"
            if 'divide' in dt:
                dwell_times += f"<Divide>{json_tt['dwell_times']['divide']}</Divide>"
            if 'crew_change' in dt:
                dwell_times += f"<CrewChange>{json_tt['dwell_times']['crew_change']}</CrewChange>"
    elif category_as_dict is not None and 'dwell_times' in category_as_dict:
        dwell_times = ''
        for dt in category_as_dict['dwell_times']:
            if 'red_signal_move_off' in dt:
                dwell_times += f"<RedSignalMoveOff>{category_as_dict['dwell_times']['red_signal_move_off']}</RedSignalMoveOff>"
            if 'station_forward' in dt:
                dwell_times += f"<StationForward>{category_as_dict['dwell_times']['station_forward']}</StationForward>"
            if 'station_reverse' in dt:
                dwell_times += f"<StationReverse>{category_as_dict['dwell_times']['station_reverse']}</StationReverse>"
            if 'terminate_forward' in dt:
                dwell_times += f"<TerminateForward>{category_as_dict['dwell_times']['terminate_forward']}</TerminateForward>"
            if 'terminate_reverse' in dt:
                dwell_times += f"<TerminateReverse>{category_as_dict['dwell_times']['terminate_reverse']}</TerminateReverse>"
            if 'join' in dt:
                dwell_times += f"<Join>{category_as_dict['dwell_times']['join']}</Join>"
            if 'divide' in dt:
                dwell_times += f"<Divide>{category_as_dict['dwell_times']['divide']}</Divide>"
            if 'crew_change' in dt:
                dwell_times += f"<CrewChange>{category_as_dict['dwell_times']['crew_change']}</CrewChange>"
    else:
        dwell_times = ''

    if 'non_ars' in json_tt:
        extras += '<NonARSOnEntry>-1</NonARSOnEntry>'
    if 'seed_group' in json_tt:
        extras += f'<SeedGroup>{json_tt["seed_group"]}</SeedGroup>'

    # Add entry point and time if needed.
    if 'entry_point' in json_tt:
        extras += f"<EntryPoint>{json_tt['entry_point']}</EntryPoint>"
        if 'entry_time' in json_tt:
            extras += f"<DepartTime>{str(common.convert_time_to_secs(json_tt['entry_time']))}</DepartTime>"
    elif 'seed_point' in json_tt:
        extras += f"<SeedPoint>{json_tt['seed_point']}</SeedPoint><Started>-1</Started>"
        if 'entry_time' in json_tt:
            extras += f"<DepartTime>{str(common.convert_time_to_secs(json_tt['entry_time']))}</DepartTime>"

    if 'increment_on_transfer' in json_tt:
        extras += f"<IncrementOnTransfer>{json_tt['increment_on_transfer']}</IncrementOnTransfer>"
    if 'class_of_service' in json_tt:
        extras += f"<ClassOfService>{json_tt['class_of_service']}</ClassOfService>"
    if 'stp' in json_tt:
        extras += f"<STP>{json_tt['stp']}</STP>"
    if 'bonus_score' in json_tt:
        extras += f"<BonusScore>{json_tt['bonus_score']}</BonusScore>"
    if 'shunt_move' in json_tt:
        extras += f"<ShuntMove>{json_tt['shunt_move']}</ShuntMove>"
    if 'shunt_phone' in json_tt:
        extras += f"<ShuntPhone>{json_tt['shunt_phone']}</ShuntPhone>"
    if 'shunt_interpose' in json_tt:
        extras += f"<ShuntInterpose>{json_tt['shunt_interpose']}</ShuntInterpose>"

    if 'shunt_times' in json_tt:
        extras += '<ShuntTimes>'
        for st in json_tt['shunt_times']:
            extras += '<ShuntTime>'
            if 'start_time' in st:
                extras += f"<StartTime>{st['start_time']}</StartTime>"
            if 'end_time' in st:
                extras += f"<EndTime>{st['end_time']}</EndTime>"
            if 'min_interval' in st:
                extras += f"<MinInterval>{st['min_interval']}</MinInterval>"
            if 'max_interval' in st:
                extras += f"<MaxInterval>{st['max_interval']}</MaxInterval>"
            extras += '</ShuntTime>'
        extras += '</ShuntTimes>'

    # Compose our string that makes up a TT.
    tt_string = tt_template.replace('${ID}', headcode).replace('${UID}', uid) \
        .replace('${AccelBrakeIndex}', accel_brake_index).replace('${Description}', description) \
        .replace('${MaxSpeed}', max_speed).replace('${isFreight}', is_freight).replace('${TrainLength}', train_length) \
        .replace('${Electrification}', electrification).replace('${OriginName}', origin_name) \
        .replace('${DestinationName}', destination_name).replace('${OriginTime}', origin_time) \
        .replace('${DestinationTime}', destination_time).replace('${OperatorCode}', operator_code) \
        .replace('${StartTraction}', start_traction).replace('${SpeedClass}', speed_class) \
        .replace('${Category}', category).replace('${Trips}', trips).replace('${DwellTimes}', dwell_times) \
        .replace('${SeedingGap}', seeding_gap).replace('${AsRequiredPercent}', as_required_percent) \
        .replace('${Extras}', extras)

    return tt_string


def build_xml_rule(json_rule: dict, locations_map: dict) -> str:
    """
    :param json_rule: json rule for a train.
    :param locations_map: map of sim locations.
    :return: XML version of rule.
    """
    RULE_NAMES_DICT = {'0': 'XAppAfterYEnt', '1': 'XAppAfterYLve', '2': 'XAppAfterYArr', '3': 'XNotIfY',
                       '4': 'XDepAfterYArr',
                       '5': 'XDepAfterYEnt', '6': 'XDepAfterYLve', '7': 'XDepAfterYJoin', '8': 'XDepAfterYDiv',
                       '9': 'XDepAfterYForm', '10': 'XYMutExc', '11': 'XAppAfterYJoin', '12': 'XAppAfterYDiv',
                       '13': 'XAppAfterYForm', '14': 'XYAlternatives'}

    for num in RULE_NAMES_DICT.keys():
        if RULE_NAMES_DICT[num] == json_rule['name']:
            rule_num = str(num)

    out = '<TimetableRule><Rule>' + rule_num + '</Rule>'
    if 'train_x' in json_rule:
        out += f"<Train>{json_rule['train_x']}</Train>"
    if 'train_y' in json_rule:
        out += f"<Train2>{json_rule['train_y']}</Train2>"
    if 'train_x_uid' in json_rule:
        out += f"<TrainUID>{json_rule['train_x_uid']}</TrainUID>"
    if 'train_y_uid' in json_rule:
        out += f"<Train2UID>{json_rule['train_y_uid']}</Train2UID>"
    if 'time' in json_rule:
        out += '<Time>' + json_rule['time'] + '</Time>'
    if 'location' in json_rule:
        location = common.find_tiploc_for_location(json_rule['location'], locations_map)
        out += '<Location>' + location + '</Location>'

    return out + '</TimetableRule>'


# Creates the file that we write the list of TTs to.
def create_xml_tt_list_file(list_of_tts: list, filename: str):
    with open(filename, 'w') as f_to_write:
        for tt in list_of_tts:
            print(tt, file=f_to_write)


def build_xml_header(header_db: MainHeaderDb) -> str:
    json_tt_header = header_db.get_header()
    if 'actual_name' in json_tt_header:
        name = json_tt_header['actual_name']
    else:
        name = json_tt_header['name']

    if 'seed_group_summary' in json_tt_header and json_tt_header['seed_group_summary'] is not None:
        sgs = json_tt_header['seed_group_summary']
    else:
        sgs = ''

    if 'train_description_template' in json_tt_header and json_tt_header['train_description_template'] is not None:
        train_description_template = json_tt_header['train_description_template']
    else:
        train_description_template = ''

    if 'description' in json_tt_header and json_tt_header['description'] is not None:
        description = json_tt_header['description']
    else:
        description = ''


    out = '<SimSigTimetable ID="' + json_tt_header['sim_id'] + '" Version="' + json_tt_header['version'] + '">' + \
          '<Name>' + name + '</Name><Description>' + description + '</Description>' + \
          '<StartTime>' + str(common.convert_time_to_secs(json_tt_header['start_time'])) + '</StartTime><FinishTime>' + \
          str(common.convert_time_to_secs(json_tt_header['finish_time'])) + \
          '</FinishTime><VMajor>' + json_tt_header['v_major'] + '</VMajor><VMinor>' + json_tt_header['v_minor'] + \
          '</VMinor><VBuild>' + json_tt_header['v_build'] + '</VBuild>' + '<TrainDescriptionTemplate>' + \
          train_description_template + '</TrainDescriptionTemplate><SeedGroupSummary>'\
          + sgs + '</SeedGroupSummary><ScenarioOptions></ScenarioOptions>'

    return out


def build_xml_list_of_tts(tt_name: str, output_filename: str, locations_map: dict, categories_map: dict,
                          use_default_category: bool):
    """
    Takes a db with json train TTs and creates an xml file with a list of all those TTs.
    This will not add any of the other stuff that goes into a Simsig xml TT.

    :param tt_name: Name of tt, used to find db file.
    :param output_filename: Name of xml file with TTs that is created.
    :param locations_map: TIPLOC map for sim locations
    :param categories_map:
    :param use_default_category: if train has default category then denotes whether we write with cat or not
    """

    tt_db = TrainTtDb(tt_name)
    xml_tts = []
    train_cat_by_id = common.make_id_key_category_map(categories_map)
    train_cat_by_desc = categories_map
    for tt in tt_db.get_all_in_db():
        print('Building xml TT for ' + tt['headcode'])
        xml_tts.append(convert_individual_json_tt_to_xml(tt, locations_map, train_cat_by_id, train_cat_by_desc,
                                                         use_default_category))

    create_xml_tt_list_file(xml_tts, output_filename)


def build_xml_list_of_rules(tt_name: str, locations_map: dict):
    rules_db = RulesDb(tt_name)
    xml_rules = []
    for rule in rules_db.get_all_in_db():
        xml_rules.append(build_xml_rule(rule, locations_map))

    return xml_rules


def convert_categories_to_xml(categories_map: dict) -> str:
    out = '<TrainCategories>'
    for category_desc in categories_map:
        out += f'<TrainCategory ID="{categories_map[category_desc]["id"]}">'
        out += f'<Description>{escape(category_desc)}</Description>'
        if 'accel_brake_index' in categories_map[category_desc]:
            out += f'<AccelBrakeIndex>{categories_map[category_desc]["accel_brake_index"]}</AccelBrakeIndex>'
        if 'is_freight' in categories_map[category_desc]:
            out += f'<IsFreight>{categories_map[category_desc]["is_freight"]}</IsFreight>'
        if 'can_use_goods_lines' in categories_map[category_desc]:
            out += f'<CanUseGoodsLines>{categories_map[category_desc]["can_use_goods_lines"]}</CanUseGoodsLines>'
        if 'max_speed' in categories_map[category_desc]:
            out += f'<MaxSpeed>{categories_map[category_desc]["max_speed"]}</MaxSpeed>'
        if 'train_length' in categories_map[category_desc]:
            out += f'<TrainLength>{categories_map[category_desc]["train_length"]}</TrainLength>'
        if 'speed_class' in categories_map[category_desc]:
            out += f'<SpeedClass>{categories_map[category_desc]["speed_class"]}</SpeedClass>'
        if 'power_to_weight_category' in categories_map[category_desc]:
            out += f'<PowerToWeightCategory>{categories_map[category_desc]["power_to_weight_category"]}</PowerToWeightCategory>'
        if 'electrification' in categories_map[category_desc]:
            out += f'<Electrification>{categories_map[category_desc]["electrification"]}</Electrification>'
        if 'dwell_times' in categories_map[category_desc]:
            out += '<DwellTimes>'
            if 'red_signal_move_off' in categories_map[category_desc]['dwell_times']:
                out += f"<RedSignalMoveOff>{categories_map[category_desc]['dwell_times']['red_signal_move_off']}</RedSignalMoveOff>"
            if 'station_forward' in categories_map[category_desc]['dwell_times']:
                out += f"<StationForward>{categories_map[category_desc]['dwell_times']['station_forward']}</StationForward>"
            if 'station_reverse' in categories_map[category_desc]['dwell_times']:
                out += f"<StationReverse>{categories_map[category_desc]['dwell_times']['station_reverse']}</StationReverse>"
            if 'terminate_forward' in categories_map[category_desc]['dwell_times']:
                out += f"<TerminateForward>{categories_map[category_desc]['dwell_times']['terminate_forward']}</TerminateForward>"
            if 'terminate_reverse' in categories_map[category_desc]['dwell_times']:
                out += f"<TerminateReverse>{categories_map[category_desc]['dwell_times']['terminate_reverse']}</TerminateReverse>"
            if 'join' in categories_map[category_desc]['dwell_times']:
                out += f'<Join>{categories_map[category_desc]["dwell_times"]["join"]}</Join>'
            if 'divide' in categories_map[category_desc]['dwell_times']:
                out += f'<Divide>{categories_map[category_desc]["dwell_times"]["divide"]}</Divide>'
            if 'crew_change' in categories_map[category_desc]['dwell_times']:
                out += f'<CrewChange>{categories_map[category_desc]["dwell_times"]["crew_change"]}</CrewChange>'
            out += '</DwellTimes>'
        else:
            out += '<DwellTimes/>'
        out += '</TrainCategory>'
    out += '</TrainCategories>'

    return out


def build_xml_list_of_seed_groups(header_db) -> str:
    list_of_sg = header_db.get_seed_groups()
    if len(list_of_sg) == 0:
        return ''

    out = '<SeedGroups>'
    for sg in list_of_sg:
        out += f"<SeedGroup><ID>{sg['id']}</ID><StartTime>{str(common.convert_time_to_secs(sg['start_time']))}</StartTime></SeedGroup>"
    out += '</SeedGroups>'
    return out


def Write_Full_Xml_Tt(tt_name: str, output_filename: str, use_default_category: bool):
    header_db = MainHeaderDb(tt_name)
    header = build_xml_header(header_db)
    categories = header_db.get_categories_map()
    locations_map = common.create_location_map_from_file(header_db.get_header()['sim_id'])[1]
    build_xml_list_of_tts(tt_name, output_filename + 'TT_List.xml', locations_map, categories, use_default_category)
    rules = build_xml_list_of_rules(tt_name, locations_map)
    seed_groups = build_xml_list_of_seed_groups(header_db)

    if os.path.exists(output_filename) is False:
        os.mkdir(output_filename)

    with open(output_filename + '/SavedTimetable.xml', 'w') as f_to_write:
        print(header, file=f_to_write)
        print(convert_categories_to_xml(categories), file=f_to_write)

        print('<Timetables>', file=f_to_write)

        f = open(output_filename + 'TT_List.xml', mode='r')
        for fl in f:
            print(fl.rstrip(), file=f_to_write)
        f.close()

        print('</Timetables>', file=f_to_write)

        if len(rules) > 0:
            print('<TimetableRules>', file=f_to_write)

            for rule in rules:
                print(rule, file=f_to_write)
            print('</TimetableRules>', file=f_to_write)

        if seed_groups != '':
            print(seed_groups, file=f_to_write)

        print('</SimSigTimetable>', file=f_to_write)

    with open(output_filename + '/TimetableHeader.xml', 'w') as f_to_write:
        print(header, file=f_to_write)
        print('</SimSigTimetable>', file=f_to_write)

    zf = zipfile.ZipFile(output_filename + ".WTT", "w")
    zf.write(output_filename + '/SavedTimetable.xml', 'SavedTimetable.xml')
    zf.write(output_filename + '/TimetableHeader.xml', 'TimetableHeader.xml')
    zf.close()

    os.remove(f'{output_filename}/SavedTimetable.xml')
    os.remove(f'{output_filename}/TimetableHeader.xml')
    os.remove(f'{output_filename}TT_List.xml')
    os.rmdir(output_filename)
