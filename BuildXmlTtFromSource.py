"""
Takes a yaml spec that gives: the usual tt headers (name of tt, simid ....), source location, source type,
filters on source, what category logic we want to use, whether to overwrite tt with same name?

Manages data extraction via parseData.py and submits Json data to a TT db.
Uses WriteXmlTt.py to create XML TT.
"""
import os

import yaml
import dbClient
import common
from customLocationLogic import CustomLogicExecutor
import parseData
import WriteXmlTt


def check_overwrite(spec_data):
    if 'overwrite_tt_with_same_name' in spec_data:
        if spec_data['overwrite_tt_with_same_name'] is False:
            if os.path.exists(f'db/{spec_data["timetable_header"]["name"]}') is True:
                raise Exception('TT already exists and flag is set to not overwrite.')


def create_dbs(sim_id: str) -> list:
    return [dbClient.MainHeaderDb(sim_id), dbClient.TrainTtDb(sim_id), dbClient.RulesDb(sim_id)]


def determine_sources(spec_data: dict, categories_map: dict, location_maps: list, custom_location_logic) -> list:
    sources, location_parsing_funct, train_parsing_funct = None, None, None

    if 'charlwoodhouse_location_pages' in spec_data:
        sources = spec_data['charlwoodhouse_location_pages']
        location_parsing_funct = lambda start, end, location_page: \
            parseData.Parse_Charlwood_House_Location_Page(start, end, location_page)
        train_parsing_funct = lambda train_link, location: \
            parseData.Parse_Charlwood_Train(categories_map, location_maps, custom_location_logic, location, train_link=train_link)

    elif 'charlwoodhouse_location_files' in spec_data:
        sources = spec_data['charlwoodhouse_location_files']
        if 'charlwood_files_root' in spec_data:
            files_root = spec_data['charlwood_files_root']
        else:
            files_root = ''

        if files_root == None:
            files_root = ''
        elif files_root != '' and files_root[-1] != '/':
            files_root += '/'

        location_parsing_funct = lambda start, end, location_page: \
            parseData.Parse_Charlwood_House_Location_File(start, end, f'{files_root}{location_page}')
        train_parsing_funct = lambda train_filepath, location: \
            parseData.Parse_Charlwood_Train(categories_map, location_maps, custom_location_logic, location,
                                            train_filepath=f'{files_root}charlwoodhouse.co.uk/rail/liverail/train/{train_filepath}')

    elif 'rtt_location_pages' in spec_data:
        sources = spec_data['rtt_location_pages']
        location_parsing_funct = lambda start, end, location_page: \
            parseData.Parse_Rtt_Location_Page(start, end, location_page)
        train_parsing_funct = lambda train_link, location: \
            parseData.Parse_Rtt_Train(categories_map, location_maps, custom_location_logic, location, train_link=train_link)

    return [sources, location_parsing_funct, train_parsing_funct]


def find_location(train: str, list_of_trains_with_source_loc: list) -> str:
    for t in list_of_trains_with_source_loc:
        if train in t[0]:
            return t[1]

    return ''


def sub_in_rule_defaults(rule):
    if 'headcode_increment' not in rule:
        rule['headcode_increment'] = 0
    if 'number_of' not in rule:
        rule['number_of'] = 1


def add_rules(rules_db, list_of_rule_specs):
    ignore = False
    list_of_rule_configs = []
    for rule in list_of_rule_specs:
        if rule == 'IGNORE':
            ignore = True
            continue
        if rule == 'IGNORE_END':
            ignore = False
            continue
        if ignore is False:
            list_of_rule_configs.append(sub_in_rule_defaults(rule))

    # TODO implement rules building (poss in another file with the old tt spec stuff)
    pass


def BuildXmlTtFromSource(name_of_spec_file: str):
    with open(f'spec_files/source_to_xml_tt_specs/{name_of_spec_file}.yaml', 'r') as stream:
        spec_data = yaml.safe_load(stream)

    check_overwrite(spec_data)

    if 'overwrite_trains' in spec_data:
        overwrite_trains = spec_data['overwrite_trains']
    else:
        overwrite_trains = False

    tt_header_map = spec_data['timetable_header']
    sim_id = tt_header_map['sim_id']
    tt_name = tt_header_map['name']

    header_db, train_db, rules_db = create_dbs(tt_name)
    location_maps = common.create_location_map_from_file(sim_id)
    categories_map = common.create_categories_map_from_yaml(spec_data['train_categories_file'])
    custom_location_logic = CustomLogicExecutor(sim_id, location_maps[1], location_maps[0])

    sources, parse_location, parse_train = determine_sources(spec_data, categories_map, location_maps, custom_location_logic)

    header_db.add_header(tt_header_map)
    header_db.add_categories_map(categories_map)

    list_of_trains = []
    list_of_trains_with_source_loc = []
    for source in sources:
        location, trains_at_location = parse_location(sources[source]['start'], sources[source]['end'], source)
        for train in trains_at_location:
            list_of_trains.append(train)
            list_of_trains_with_source_loc.append([train, location])

    set_of_trains = set(list_of_trains)

    for train in set_of_trains:
        location = find_location(train, list_of_trains_with_source_loc)

        if location != '':
            parsed_train = parse_train(train, location)
            if parsed_train is not None:
                if overwrite_trains is True:
                    train_db.add_tt(parsed_train)
                else:
                    train_db.add_tt_if_not_present(parsed_train)

    if 'rules' in spec_data:
        add_rules(rules_db, spec_data['rules'])

    WriteXmlTt.Write_Full_Xml_Tt(tt_name, tt_name, True)
