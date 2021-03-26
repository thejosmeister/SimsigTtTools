"""
For building up a list of train TTs to insert into a Simsig xml TT.
"""
from jsonTimetableCreator import create_json_timetables_with_spec_entry, create_json_rules_with_spec_entry
from dbClient import *


def build_list_of_tts(list_of_tt_specs: list, tt_name: str, cat_file_location: str, overwrite_old_tts: bool):
    """
    Will take a list of a specs for multiple TTs and create json TTs for each one and then store them in a TinyDb.

    :param list_of_tt_specs: List containing TT spec dicts.
    :param tt_name: Name of TT that will indicate where json TTs will be stored.
    :param cat_file_location: Location of file containing train categories.
    :param overwrite_old_tts: Do we want to overwrite any TTs already present in the db.
    """

    json_tt_list_for_file = []

    for timetable_spec in list_of_tt_specs:
        print('Building json TT for ' + timetable_spec['headcode_template'])
        for tt in create_json_timetables_with_spec_entry(timetable_spec, cat_file_location):
            json_tt_list_for_file.append(tt)

    tt_db = TrainTtDb(tt_name)

    if overwrite_old_tts is True:
        for tt in json_tt_list_for_file:
            tt_db.add_tt(tt)
    else:
        for tt in json_tt_list_for_file:
            tt_db.add_tt_if_not_present(tt)


def build_list_of_rules(list_of_rule_specs: list, tt_name: str, overwrite_old_rules: bool):
    json_rule_list_for_file = []

    for rule_spec in list_of_rule_specs:
        print('Building json Rule for ' + rule_spec['train_x'])
        for rule in create_json_rules_with_spec_entry(rule_spec):
            json_rule_list_for_file.append(rule)

    tt_db = RulesDb(tt_name)

    if overwrite_old_rules is True:
        for rule in json_rule_list_for_file:
            tt_db.add_rule(rule)
    else:
        for rule in json_rule_list_for_file:
            tt_db.add_rule_if_not_present(rule)
