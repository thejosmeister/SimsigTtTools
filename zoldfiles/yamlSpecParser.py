"""
Will parse a yaml TT spec
"""
from translateTimesAndLocations import convert_time_to_secs
import yaml


def sub_in_tt_defaults_etc(timetable, defaults, baseFilePaths):
    for default in defaults.keys():
        if default not in timetable:
            timetable[default] = defaults[default]

    for baseFilePath in baseFilePaths.keys():
        timetable[baseFilePath] = baseFilePaths[baseFilePath] + timetable[baseFilePath]

    return timetable


def sub_in_rule_defaults_etc(rule, defaults):
    for default in defaults.keys():
        if default not in rule:
            rule[default] = defaults[default]

    return rule


def parse_yaml_tt_spec(config_file_location: str) -> list:
    with open(config_file_location, 'r') as stream:
        yaml_data = yaml.safe_load(stream)

    if 'timetable_header' in yaml_data:
        header = yaml_data['timetable_header']
        header['start_time'] = str(convert_time_to_secs(header['start_time']))
        header['finish_time'] = str(convert_time_to_secs(header['finish_time']))
    else:
        header = None

    if 'train_categories_file' in yaml_data:
        categories = yaml_data['train_categories_file']
    else:
        categories = None

    list_of_tt_configs = []
    if 'timetables' in yaml_data:
        ignore = False
        for timetable in yaml_data['timetables']:
            if timetable == 'IGNORE':
                ignore = True
                continue
            if timetable == 'IGNORE_END':
                ignore = False
                continue
            if ignore is False:
                list_of_tt_configs.append(sub_in_tt_defaults_etc(timetable, yaml_data['tt_defaults'], yaml_data['base_file_paths']))

    list_of_rule_configs = []
    if 'rules' in yaml_data:
        ignore = False
        for rule in yaml_data['rules']:
            if rule == 'IGNORE':
                ignore = True
                continue
            if rule == 'IGNORE_END':
                ignore = False
                continue
            if ignore is False:
                list_of_rule_configs.append(sub_in_rule_defaults_etc(rule, yaml_data['rule_defaults']))

    return [header, categories, list_of_tt_configs, list_of_rule_configs]