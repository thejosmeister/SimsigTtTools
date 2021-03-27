"""
For building up a list of train TTs to insert into a Simsig xml TT.
"""
from tiplocDictCreator import pull_train_categories_out_of_xml_string, pull_train_categories_out_of_xml_string_by_id
from xmlTimetableCreator import convert_individual_json_tt_to_xml, build_xml_rule
from dbClient import *
import os
import zipfile


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
    out = '<SimSigTimetable ID="' + json_tt_header['id'] + '" Version="' + json_tt_header['version'] + '">' + \
          '<Name>' + name + '</Name><Description>' + json_tt_header['description'] + '</Description>' + \
          '<StartTime>' + json_tt_header['start_time'] + '</StartTime><FinishTime>' + json_tt_header['finish_time'] + \
          '</FinishTime><VMajor>' + json_tt_header['v_major'] + '</VMajor><VMinor>' + json_tt_header['v_minor'] + \
          '</VMinor><VBuild>' + json_tt_header['v_build'] + '</VBuild>' + '<TrainDescriptionTemplate>' + \
          json_tt_header['train_description_template'] + \
          '</TrainDescriptionTemplate><SeedGroupSummary></SeedGroupSummary><ScenarioOptions></ScenarioOptions>'

    return out


def build_xml_list_of_tts(tt_name: str, output_filename: str, sim_locations_file: str, categories_string: str):
    """
    Takes a db with json train TTs and creates an xml file with a list of all those TTs.
    This will not add any of the other stuff that goes into a Simsig xml TT.

    :param categories_string:
    :param tt_name: Name of tt, used to find db file.
    :param output_filename: Name of xml file with TTs that is created.
    :param sim_locations_file: Name of file containing TIPLOC map on sim locations
    """

    tt_db = TrainTtDb(tt_name)
    xml_tts = []
    train_cat_by_id = pull_train_categories_out_of_xml_string_by_id(categories_string)
    train_cat_by_desc = pull_train_categories_out_of_xml_string(categories_string)
    for tt in tt_db.get_all_in_db():
        print('Building xml TT for ' + tt['uid'])
        xml_tts.append(convert_individual_json_tt_to_xml(tt, 'sim_location_files/' + sim_locations_file, train_cat_by_id, train_cat_by_desc))

    create_xml_tt_list_file(xml_tts, output_filename)


def build_xml_list_of_rules(tt_name: str, sim_locations_file: str):
    rules_db = RulesDb(tt_name)
    xml_rules = []
    for rule in rules_db.get_all_in_db():
        xml_rules.append(build_xml_rule(rule, 'sim_location_files/' + sim_locations_file))

    return xml_rules


def build_full_xml_tt(tt_name: str, output_filename: str, sim_locations_file: str):
    header_db = MainHeaderDb(tt_name)
    header = build_xml_header(header_db)
    categories = header_db.get_categories_string()
    build_xml_list_of_tts(tt_name, output_filename + 'TT_List.xml', sim_locations_file, categories)
    rules = build_xml_list_of_rules(tt_name, sim_locations_file)

    if os.path.exists(output_filename) is False:
        os.mkdir(output_filename)

    with open(output_filename + '/SavedTimetable.xml', 'w') as f_to_write:
        print(header, file=f_to_write)
        print(categories, file=f_to_write)

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

    zf = zipfile.ZipFile( output_filename + ".WTT", "w")
    zf.write(output_filename + '/SavedTimetable.xml', 'SavedTimetable.xml')
    zf.write(output_filename + '/TimetableHeader.xml', 'TimetableHeader.xml')
    zf.close()