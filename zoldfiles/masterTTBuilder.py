from jsonTimetableListBuilder import build_list_of_tts, build_list_of_rules
from xmlTimetableBuilder import build_xml_list_of_tts, build_full_xml_tt
from yamlSpecParser import parse_yaml_tt_spec
from dbClient import MainHeaderDb


def read_cat_file(categories_file_location: str) -> str:
    f = open(categories_file_location, mode='r')
    out = ''
    for fl in f:
        out += fl.rstrip()
    f.close()
    return out


def build_complete_tt(tt_name: str, locations_filename: str, xml_output_filename: str,
                      overwrite_existing_trains_and_rules: bool):
    [header, categories, list_of_tt_configs, list_of_rule_configs] = parse_yaml_tt_spec(
        'simsig_timetables/{}/{}.yaml'.format(tt_name, tt_name))

    header_db = MainHeaderDb(tt_name)
    header_db.add_header(header)
    header_db.add_categories_string(read_cat_file(categories))

    build_list_of_tts(list_of_tt_configs, tt_name, categories, overwrite_existing_trains_and_rules)
    if len(list_of_rule_configs) > 0:
        build_list_of_rules(list_of_rule_configs, tt_name, overwrite_existing_trains_and_rules)

    build_full_xml_tt(tt_name, xml_output_filename, locations_filename)


def build_xml_tt_list_from_spec(tt_name: str, locations_filename: str, xml_output_filename: str,
                                overwrite_existing_trains: bool):
    [header, categories, list_of_tt_configs, list_of_rule_configs] = parse_yaml_tt_spec(
        'simsig_timetables/{}/{}.yaml'.format(tt_name, tt_name))
    build_list_of_tts(list_of_tt_configs, tt_name, categories, overwrite_existing_trains)
    build_xml_list_of_tts(tt_name, xml_output_filename, locations_filename)


build_complete_tt('swindid_diversions_feb_21', 'swindid.txt', 'swindid_diversions_feb_21', True)
