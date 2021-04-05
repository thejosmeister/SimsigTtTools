"""
Writes XML TT from what is stored in Json TT db.
"""
from dbClient import *
import os
import zipfile
import common
from xml.sax.saxutils import escape


# Will sub in TIPLOC codes for locations in the sim
def sub_in_tiploc(sorted_locations: list, tiploc_dict: dict) -> list:
    out = []
    for l in sorted_locations:
        for t in tiploc_dict.keys():
            if l['location'] in tiploc_dict[t]:
                l['location'] = str(t)
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
    for activity in location['activities'].keys():
        f = open('templates/activities/' + str(activity) + 'Template.txt', "r")
        if 'crewChange' in str(activity):
            for fl in f:
                out += fl.rstrip()
        else:
            for fl in f:
                uid_to_insert = location['activities'][activity]
                out += fl.rstrip().replace('${UID}', uid_to_insert)
        f.close()

    return out + '</Activities>'


def create_xml_trip(location: dict) -> str:
    out = '<Trip><Location>' + location['location'] + '</Location>'
    if 'dep' in location:
        out += '<DepPassTime>' + str(common.convert_time_to_secs(location['dep'])) + '</DepPassTime>'
        if 'arr' not in location and 'isOrigin' not in location:
            out += '<IsPassTime>-1</IsPassTime>'
    if 'arr' in location:
        out += '<ArrTime>' + str(common.convert_time_to_secs(location['arr'])) + '</ArrTime>'
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
    trips = ''.join([create_xml_trip(l) for l in locations_on_sim])

    # Sort all the parameters to plug in to template.
    accel_brake_index = json_tt['accel_brake_index']
    uid = json_tt['uid']
    headcode = json_tt['headcode']
    max_speed = json_tt['max_speed']
    is_freight = json_tt['is_freight']
    train_length = json_tt['train_length']
    electrification = json_tt['electrification']
    origin_name = escape(json_tt['origin_name'])
    destination_name = escape(json_tt['destination_name'])
    origin_time = str(common.convert_time_to_secs(json_tt['origin_time']))
    description = escape(json_tt['description'])
    destination_time = str(common.convert_time_to_secs(json_tt['destination_time']))
    operator_code = json_tt['operator_code']
    start_traction = json_tt['start_traction']
    speed_class = json_tt['speed_class']
    extras = ''

    if 'standard diesel freight' == json_tt['category'] and use_default_category is True:
        # Train has default category
        category = train_cat_by_desc[json_tt['category']]['id']
    elif 'A0000001' == json_tt['category'] and use_default_category is True:
        # Train has default category
        category = json_tt['category']
    elif json_tt['category'] in train_cat_by_id:
        category = json_tt['category']
    else:
        category = train_cat_by_desc[json_tt['category']]['id']

    if 'dwell_times' in json_tt:
        dwell_times = '<Join>' + json_tt['dwell_times']['join'] + '</Join><Divide>' + \
                      json_tt['dwell_times']['divide'] + '</Divide><CrewChange>' + \
                      json_tt['dwell_times']['crew_change'] + '</CrewChange>'
    else:
        dwell_times = ''

    if 'non_ars' in json_tt:
        extras += '<NonARSOnEntry>-1</NonARSOnEntry>'

    # Compose our string that makes up a TT.
    tt_string = tt_template.replace('${ID}', headcode).replace('${UID}', uid) \
        .replace('${AccelBrakeIndex}', accel_brake_index).replace('${Description}', description) \
        .replace('${MaxSpeed}', max_speed).replace('${isFreight}', is_freight).replace('${TrainLength}', train_length) \
        .replace('${Electrification}', electrification).replace('${OriginName}', origin_name) \
        .replace('${DestinationName}', destination_name).replace('${OriginTime}', origin_time) \
        .replace('${DestinationTime}', destination_time).replace('${OperatorCode}', operator_code) \
        .replace('${StartTraction}', start_traction).replace('${SpeedClass}', speed_class) \
        .replace('${Category}', category).replace('${Trips}', trips).replace('${DwellTimes}', dwell_times) \
        .replace('${Extras}', extras)

    # Add entry point and time if needed.
    if 'entry_point' in json_tt:
        entry_point = json_tt['entry_point']
        depart_time = str(common.convert_time_to_secs(json_tt['entry_time']))
        return tt_string.replace('${EntryPoint}', entry_point).replace('${DepartTime}', depart_time)
    elif 'seed_point' in json_tt:
        seed_point = json_tt['seed_point']
        depart_time = str(common.convert_time_to_secs(json_tt['entry_time']))
        return tt_string.replace('${SeedPoint}', seed_point).replace('${DepartTime}', depart_time)
    else:
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

    out = '<TimetableRule><Rule>' + rule_num + '</Rule><TrainUID>' + json_rule['train_x'] + '</TrainUID>' \
          + '<Train2UID>' + json_rule['train_y'] + '</Train2UID>'
    if 'time' in json_rule:
        out += '<Time>' + json_rule['time'] + '</Time>'
    if 'location' in json_rule:
        for tiploc in locations_map:
            if json_rule['location'] in locations_map[tiploc]:
                location = str(tiploc)
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
    out = '<SimSigTimetable ID="' + json_tt_header['sim_id'] + '" Version="' + json_tt_header['version'] + '">' + \
          '<Name>' + name + '</Name><Description>' + json_tt_header['description'] + '</Description>' + \
          '<StartTime>' + str(common.convert_time_to_secs(json_tt_header['start_time'])) + '</StartTime><FinishTime>' + \
          str(common.convert_time_to_secs(json_tt_header['finish_time'])) + \
          '</FinishTime><VMajor>' + json_tt_header['v_major'] + '</VMajor><VMinor>' + json_tt_header['v_minor'] + \
          '</VMinor><VBuild>' + json_tt_header['v_build'] + '</VBuild>' + '<TrainDescriptionTemplate>' + \
          json_tt_header['train_description_template'] + \
          '</TrainDescriptionTemplate><SeedGroupSummary></SeedGroupSummary><ScenarioOptions></ScenarioOptions>'

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
        xml_tts.append(convert_individual_json_tt_to_xml(tt, locations_map, train_cat_by_id, train_cat_by_desc, use_default_category))

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
        out += f'<Description>{category_desc}</Description>'
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


def Write_Full_Xml_Tt(tt_name: str, output_filename: str, use_default_category: bool):
    header_db = MainHeaderDb(tt_name)
    header = build_xml_header(header_db)
    categories = header_db.get_categories_map()
    locations_map = common.create_location_map_from_file(header_db.get_header()['sim_id'])[1]
    build_xml_list_of_tts(tt_name, output_filename + 'TT_List.xml', locations_map, categories, use_default_category)
    rules = build_xml_list_of_rules(tt_name, locations_map)

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
