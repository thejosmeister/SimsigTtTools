"""
Will create an xml TT for a json train TT
"""
import unittest

from tiplocDictCreator import create_tiploc_dict
from translateTimesAndLocations import convert_time_to_secs, convert_sec_to_time, sub_in_tiploc


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
        out += '<DepPassTime>' + str(convert_time_to_secs(location['dep'])) + '</DepPassTime>'
        if 'arr' not in location and 'isOrigin' not in location:
            out += '<IsPassTime>-1</IsPassTime>'
    if 'arr' in location:
        out += '<ArrTime>' + str(convert_time_to_secs(location['arr'])) + '</ArrTime>'
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


def convert_individual_json_tt_to_xml(json_tt: dict, tiploc_location: str, train_cat_by_id: dict, train_cat_by_desc: dict) -> str:
    """
    Takes a json timetable for a train and produces an xml one for insertion into a Simsig xml TT.
    :param train_cat_by_desc:
    :param train_cat_by_id:
    :param json_tt: json timetable for a train.
    :param tiploc_location: will give a map of sim locations.
    :return: XML string with TT.
    """

    tt_template = read_in_tt_template(json_tt['tt_template'])
    locations_on_sim = sub_in_tiploc(json_tt['locations'], create_tiploc_dict(tiploc_location)[1])
    trips = ''.join([create_xml_trip(l) for l in locations_on_sim])

    # Sort all the parameters to plug in to template.
    accel_brake_index = json_tt['accel_brake_index']
    uid = json_tt['uid']
    headcode = json_tt['headcode']
    max_speed = json_tt['max_speed']
    is_freight = json_tt['is_freight']
    train_length = json_tt['train_length']
    electrification = json_tt['electrification']
    origin_name = json_tt['origin_name']
    destination_name = json_tt['destination_name']
    origin_time = str(convert_time_to_secs(json_tt['origin_time']))
    description = json_tt['description']
    destination_time = str(convert_time_to_secs(json_tt['destination_time']))
    operator_code = json_tt['operator_code']
    start_traction = json_tt['start_traction']
    speed_class = json_tt['speed_class']
    extras = ''

    if json_tt['category'] in train_cat_by_id:
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
        .replace('${Category}', category).replace('${Trips}', trips).replace('${DwellTimes}', dwell_times)\
        .replace('${Extras}', extras)

    # Add entry point and time if needed.
    if 'entry_point' in json_tt:
        entry_point = json_tt['entry_point']
        depart_time = str(convert_time_to_secs(json_tt['entry_time']))
        return tt_string.replace('${EntryPoint}', entry_point).replace('${DepartTime}', depart_time)
    elif 'seed_point' in json_tt:
        seed_point = json_tt['seed_point']
        depart_time = str(convert_time_to_secs(json_tt['entry_time']))
        return tt_string.replace('${SeedPoint}', seed_point).replace('${DepartTime}', depart_time)
    else:
        return tt_string



def build_xml_rule(json_rule: dict, tiploc_location: str) -> str:
    """

    :param json_rule: json rule for a train.
    :param tiploc_location: will give a map of sim locations.
    :return:
    """
    RULE_NAMES_DICT = {'0': 'XAppAfterYEnt', '1': 'XAppAfterYLve', '2': 'XAppAfterYArr', '3': 'XNotIfY', '4': 'XDepAfterYArr',
                       '5': 'XDepAfterYEnt', '6': 'XDepAfterYLve', '7': 'XDepAfterYJoin', '8': 'XDepAfterYDiv',
                       '9': 'XDepAfterYForm', '10': 'XYMutExc', '11': 'XAppAfterYJoin', '12': 'XAppAfterYDiv',
                       '13': 'XAppAfterYForm', '14': 'XYAlternatives'}
    tiploc_dict = create_tiploc_dict(tiploc_location)[1]

    for num in RULE_NAMES_DICT.keys():
        if RULE_NAMES_DICT[num] == json_rule['name']:
            rule_num = str(num)

    out = '<TimetableRule><Rule>' + rule_num + '</Rule><TrainUID>' + json_rule['train_x'] + '</TrainUID>' \
          + '<Train2UID>' + json_rule['train_y'] + '</Train2UID>'
    if 'time' in json_rule:
        out += '<Time>' + json_rule['time'] + '</Time>'
    if 'location' in json_rule:
        for tiploc in tiploc_dict:
            if json_rule['location'] in tiploc_dict[tiploc]:
                location = str(tiploc)
        out += '<Location>' + location + '</Location>'

    return out + '</TimetableRule>'

# UTs
class TestTimetableCreator(unittest.TestCase):

    def test_create_xml_trip(self):
        location = {'arr': '0001', 'line': 'UM', 'location': 'SDON', 'plat': '1', 'activities': {'trainBecomes': '5G09'}}
        trip = '<Trip><Location>SDON</Location><ArrTime>60</ArrTime><Platform>1</Platform><Line>UM</Line><Activities>'\
               '<Activity><Activity>0</Activity><AssociatedUID>5G09</AssociatedUID></Activity></Activities></Trip>'

        self.assertEqual(create_xml_trip(location), trip)

        location = {'dep': '0001', 'line': 'UM', 'location': 'SDON'}
        trip = '<Trip><Location>SDON</Location><DepPassTime>60</DepPassTime><IsPassTime>-1</IsPassTime><Line>UM' \
               '</Line></Trip>'

        self.assertEqual(create_xml_trip(location), trip)
