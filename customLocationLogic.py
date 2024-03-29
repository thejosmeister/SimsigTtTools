"""
For executing custom (and some general) logic on sim locations for a train.
"""
import re

import yaml
import common


class CustomLogicExecutor:

    def __init__(self, sim_id: str, locations_map: dict, entry_points_map: dict):
        self.locations_map = locations_map
        self.entry_points_map = entry_points_map

        # get custom specs
        custom_specs_location = f'spec_files/sim_custom_location_logic/{sim_id}.yaml'
        with open(custom_specs_location, 'r') as stream:
            self.custom_specs = yaml.safe_load(stream)

        # May instantiate dbs here in future

    def Perform_Custom_Logic(self, train_locations: list, potential_entry: str, potential_entry_time: str) -> list:
        """
        :param train_locations: prospective train locations to undergo logic.
        :param potential_entry: the potential entry point for the train
        :param potential_entry_time: the associated potential entry time.
        :return: [ entry_point?, entry_time?, tt_template, location_list ]
        """

        # Look to see if entry point has custom logic
        entry_location = self.get_entry_location_in_train_locs(potential_entry, train_locations)
        if 'entry_point_rules' in self.custom_specs and potential_entry in self.custom_specs['entry_point_rules']:
            entry_point, entry_time, \
            tt_template, train_locations = self.apply_custom_entry_logic(train_locations, entry_location,
                                                                         potential_entry_time,
                                                                         potential_entry)
        # If not then apply default
        else:
            entry_point, entry_time, \
            tt_template, train_locations = self.apply_generic_entry_logic(train_locations, entry_location,
                                                                          potential_entry_time,
                                                                          potential_entry)

        # For each location in custom logic apply custom rules
        if 'location_rules' in self.custom_specs:
            train_locations = self.apply_location_logic(entry_point, train_locations)

        return [entry_point, entry_time, tt_template, train_locations]

    def apply_custom_entry_logic(self, train_locations, entry_location, entry_time, potential_entry):
        rules_for_entry = self.custom_specs['entry_point_rules'][potential_entry]

        for rule in rules_for_entry:
            if rule == 'list_to_delete_if_before':
                train_locations = self.list_to_delete_if_before(
                    rules_for_entry[rule], entry_location, entry_time, train_locations)
                return self.apply_generic_entry_logic(train_locations, entry_location, entry_time, potential_entry)
            if rule == 'if_later_location_matching':
                return self.if_later_location_matching(rules_for_entry[rule], entry_location, entry_time,
                                                       train_locations, potential_entry)
            if rule == 'if_entry_location_matching':
                return self.if_entry_location_matching(rules_for_entry[rule], entry_location, entry_time,
                                                       train_locations, potential_entry)

        return None

    def list_to_delete_if_before(self, list_to_delete, entry_location, entry_time, train_locations):
        """
        Will delete any of these found before the entry point location.
        """
        if entry_location is None and entry_time is None:
            return train_locations

        if entry_location is None:
            for location in list_to_delete:
                if self.x_after_time(location, entry_time, train_locations) is False:
                    train_locations = self.remove_nth_location(location, 1, train_locations)
        else:
            for location in list_to_delete:
                if self.x_before_y(location, entry_location, train_locations) is True:
                    train_locations = self.remove_nth_location(location, 1, train_locations)

        return train_locations

    def get_entry_location_in_train_locs(self, potential_entry, train_locations):
        """
        Returns an associated entry location name if found.
        """
        if potential_entry is not None:
            tiploc_for_entry = self.entry_points_map[potential_entry]['assoc_sim_location']
            readable_entry_name = common.find_readable_location(tiploc_for_entry, self.locations_map)

            entry_location = self.get_entry_location_in_list(readable_entry_name, train_locations)

            if entry_location is not None:
                return entry_location['location']
        return None

    def get_entry_location_in_list(self, readable_entry_name, train_locations):
        """
        Returns the whole location, not just the name.
        """
        loc_list = list(filter(lambda x: x['location'] == readable_entry_name, train_locations))
        if len(loc_list) > 0:
            return loc_list[0]
        return None

    def x_before_y(self, x, y, train_locations):
        """
        Will return none if cant find either in locations.
        Will return false if same location.
        """
        x_readable = common.find_readable_location(x, self.locations_map)
        y_readable = common.find_readable_location(y, self.locations_map)

        x_pos = -1
        y_pos = -1

        for i in range(len(train_locations)):
            if train_locations[i]['location'] == x_readable:
                x_pos = i
            if train_locations[i]['location'] == y_readable:
                y_pos = i

        if x_pos == -1 or y_pos == -1:
            print('One of values not in locations')
            return None

        return x_pos < y_pos

    def x_after_time(self, x, time, train_locations):
        """
        Will return false if cant find x in locations.
        Will return false if same time.
        """
        x_readable = common.find_readable_location(x, self.locations_map)
        x_time = None
        for l in train_locations:
            if l['location'] == x_readable:
                if 'dep' in l:
                    x_time = l['dep']
                elif 'arr' in l:
                    x_time = l['arr']

        if x_time is None:
            return False

        time_as_num = float(time)

        return time_as_num < float(x_time)

    def remove_all_of_location(self, location_to_remove, train_locations):
        standard_location_to_remove = common.find_readable_location(location_to_remove, self.locations_map)
        return list(filter(lambda x: x['location'] != standard_location_to_remove, train_locations))

    def remove_nth_location(self, location_to_remove, nth_time, train_locations):
        standard_location_to_remove = common.find_readable_location(location_to_remove, self.locations_map)
        count_times_seen = 0
        new_locations = train_locations.copy()
        for i in range(len(train_locations)):
            if train_locations[i]['location'] == standard_location_to_remove:
                count_times_seen += 1
                if count_times_seen == nth_time:
                    new_locations.pop(i)
                    return new_locations
        return new_locations

    def apply_generic_entry_logic(self, train_locations, entry_location, potential_entry_time, potential_entry):
        """
        If potential entry is 1st location then capture dep time as entry time and delete location.
        If potential entry is not 1st location (implicitly no custom) then assume train starts on sim.
        If potential entry does not match to any locations then assume at start and take nominal entry time from 1st location.
        If no potential entry then assume starts on sim.
        """

        # If we cant find anything then bail out with a default
        if entry_location is None and potential_entry is not None:
            return [potential_entry, potential_entry_time,
                    'templates/timetables/defaultTimetable.txt', train_locations]

        # If entry is first location then we delete first location and are done.
        if train_locations[0]['location'] == entry_location:
            train_locations = self.remove_nth_location(entry_location, 1, train_locations)
            return [potential_entry, potential_entry_time,
                    'templates/timetables/defaultTimetable.txt', train_locations]

        # Assume starts on sim.
        return [None, None, 'templates/timetables/defaultTimetable.txt', train_locations]

    def if_later_location_matching(self, rule_root, entry_location, entry_time, train_locations, potential_entry):
        """
        Applies some then clauses if there are locations after the potential entry time that satisfy conditions.
        """
        later_locations = list(
            filter(lambda x: self.x_after_time(x['location'], entry_time, train_locations) is True, train_locations))

        if len(later_locations) > 0 and self.rule_conditions_are_met(rule_root['conditions'], potential_entry,
                                                                     later_locations):
            return self.apply_entry_then_clause(rule_root['then'], entry_location, entry_time, train_locations,
                                                potential_entry)
        return self.apply_generic_entry_logic(train_locations, entry_location, entry_time, potential_entry)

    def rule_conditions_are_met(self, conditions, entry_point, train_locations):
        condition_met = True
        for condition in conditions:
            if condition == 'OR':
                if condition_met is True:
                    return True
                condition_met = True
                continue
            if condition_met is False:
                continue
            if self.is_condition_met(condition, entry_point, train_locations) is False:
                condition_met = False
        return condition_met

    def is_condition_met(self, condition, entry_point, train_locations):
        if 'entry_point' in condition:
            c_entry = condition['entry_point']
            if c_entry[0] == '!':
                return c_entry[1:] != entry_point
            return c_entry == entry_point

        if 'location' in condition:
            readable_location = common.find_readable_location(condition['location'], self.locations_map)
            if readable_location != '':
                condition['location'] = readable_location
        for location in train_locations:
            if all(self.is_property_in_condition_satisfied(prop, condition[prop], location) for prop in
                   condition) is True:
                return True
        return False

    def is_property_in_condition_satisfied(self, prop, prop_value, location):
        """
        Is a basic equals unless a '!' char is at the start of field or value.
        """
        if prop[0] == '!':
            if prop[1:] in location:
                return False
            return True

        # True if val in location and not equal, false if equal or prop not in location
        if prop_value[0] == '!':
            if prop in location:
                if location[prop] == prop_value[1:]:
                    return False
                return True
            return False

        if prop in location and prop_value == location[prop]:
            return True

        return False

    def apply_entry_then_clause(self, then_clauses, entry_location, entry_time, train_locations, potential_entry):
        # TODO refactor this method and apply_locations_then_clause to use common code.
        for clause in then_clauses:
            if 'entry_point' in clause:
                potential_entry = clause['entry_point']
            if 'entry_time' in clause:
                if re.match('\\d{4}', clause['entry_time']) is not None:
                    entry_time = clause['entry_time']
                else:
                    entry_time = self.determine_entry_time_from_location(clause['entry_time'], train_locations,
                                                                         entry_time)
            if 'remove_1st_of' in clause:
                for l_to_remove in clause['remove_1st_of']:
                    train_locations = self.remove_nth_location(l_to_remove, 1, train_locations)
            if 'remove_all_of' in clause:
                for l_to_remove in clause['remove_all_of']:
                    train_locations = self.remove_all_of_location(l_to_remove, train_locations)
            if 'modify_location' in clause:
                train_locations = self.modify_location(clause['modify_location'], train_locations)
            if 'remove_props_from_location' in clause:
                train_locations = self.remove_props_from_location(clause['remove_props_from_location'], train_locations)

        return [potential_entry, entry_time, 'templates/timetables/defaultTimetable.txt', train_locations]

    def if_entry_location_matching(self, rule, entry_location, entry_time, train_locations, potential_entry):
        check_entry_location = list(filter(lambda x: x['location'] == entry_location, train_locations))
        if len(check_entry_location) > 0:
            if self.rule_conditions_are_met(rule['conditions'], potential_entry, [check_entry_location[0]]):
                return self.apply_entry_then_clause(rule['then'], entry_location, entry_time, train_locations,
                                                    potential_entry)
        return self.apply_generic_entry_logic(train_locations, entry_location, entry_time, potential_entry)

    def apply_location_logic(self, entry_point, train_locations):
        for location in self.custom_specs['location_rules']:
            for rule in self.custom_specs['location_rules'][location]:
                if 'if_x_y_concurrent' in rule:
                    train_locations = self.apply_x_y_concurrent(rule['if_x_y_concurrent'], entry_point, train_locations)
                if 'if_particular_present' in rule:
                    train_locations = self.apply_if_particular_present(rule['if_particular_present'], entry_point,
                                                                       train_locations)
                if 'remove_location' in rule:
                    train_locations = self.apply_remove_location(rule['remove_location'], entry_point, train_locations)
        return train_locations

    def apply_x_y_concurrent(self, rule_map, entry_point, train_locations):
        if 'entry_point' in rule_map:
            c_entry = rule_map['entry_point']
            if c_entry[0] == '!' and c_entry[1:] == entry_point:
                return train_locations
            if entry_point != c_entry:
                return train_locations
            amount_of_locations = len(rule_map) - 2
        else:
            amount_of_locations = len(rule_map) - 1

        location_conditions = []
        for i in range(1, amount_of_locations + 1):
            location_conditions.append(rule_map[f'location_{i}_conditions'][0])

        if len(train_locations) < 2:
            return train_locations

        # check all concurrent
        loc_1_index = self.are_x_y_concurrent(location_conditions[0]['location'], location_conditions[1]['location'],
                                              train_locations)

        if loc_1_index > -1 and amount_of_locations > 2:
            next_index = loc_1_index + 2
            for i in range(2, amount_of_locations):
                if self.is_location_at_index(location_conditions[i]['location'], next_index, train_locations) is False:
                    return train_locations
                next_index += 1

        # check all meet conditions
        location_index = loc_1_index
        for location_condition in location_conditions:
            if self.is_condition_met(location_condition, entry_point, [train_locations[location_index]]) is False:
                return train_locations
            location_index += 1

        # Apply then clauses
        return self.apply_locations_then_clause(rule_map['then'], train_locations)

    def is_location_at_index(self, location_name, index, train_locations):
        if index > len(train_locations) - 1:
            return False

        return train_locations[index]['location'] == common.find_readable_location(location_name, self.locations_map)

    def apply_if_particular_present(self, rule, entry_point, train_locations):
        if self.rule_conditions_are_met(rule['conditions'], entry_point, train_locations) is True:
            train_locations = self.apply_locations_then_clause(rule['then'], train_locations)

        return train_locations

    def are_x_y_concurrent(self, location1, location2, train_locations):
        """
        Returns index of location 1 if condition satisfied, o.w. will return -1
        """
        readable_l1 = common.find_readable_location(location1, self.locations_map)
        readable_l2 = common.find_readable_location(location2, self.locations_map)

        if any(readable_l1 == l['location'] for l in train_locations) is False or any(
                readable_l2 == l['location'] for l in train_locations) is False:
            return -1

        for i in range(len(train_locations) - 1):
            if train_locations[i]['location'] == readable_l1 and train_locations[i + 1]['location'] == readable_l2:
                return i

        return -1

    def apply_locations_then_clause(self, then_clauses, train_locations):
        for clause in then_clauses:
            if 'remove_1st_of' in clause:
                for l_to_remove in clause['remove_1st_of']:
                    train_locations = self.remove_nth_location(l_to_remove, 1, train_locations)
            if 'remove_all_of' in clause:
                for l_to_remove in clause['remove_all_of']:
                    train_locations = self.remove_all_of_location(l_to_remove, train_locations)
            if 'modify_location' in clause:
                train_locations = self.modify_location(clause['modify_location'], train_locations)
            if 'remove_props_from_location' in clause:
                train_locations = self.remove_props_from_location(clause['remove_props_from_location'], train_locations)

        return train_locations

    def modify_location(self, location_modifications, train_locations):
        location_modifications_copy = location_modifications.copy()
        if 'location' in location_modifications_copy:
            readable_l = common.find_readable_location(location_modifications_copy.pop('location'), self.locations_map)

            for l in train_locations:
                if l['location'] == readable_l:
                    for prop in location_modifications_copy:
                        l[prop] = location_modifications[prop]

        elif 'new_location' in location_modifications_copy:
            new_readable_l = common.find_readable_location(location_modifications_copy.pop('new_location'),
                                                           self.locations_map)
            old_readable_l = common.find_readable_location(location_modifications_copy.pop('old_location'),
                                                           self.locations_map)

            for l in train_locations:
                if l['location'] == old_readable_l:
                    l['location'] = new_readable_l
                    for prop in location_modifications_copy:
                        l[prop] = location_modifications[prop]

        return train_locations

    def remove_props_from_location(self, location_with_props, train_locations):
        readable_l = common.find_readable_location(location_with_props['location'], self.locations_map)

        for l in train_locations:
            if l['location'] == readable_l:
                for prop in location_with_props['props']:
                    l.pop(prop)

        return train_locations

    def apply_remove_location(self, rule_map, entry_point, train_locations):
        if 'other_conditions' in rule_map:
            condtions = rule_map['other_conditions']
        else:
            condtions = []

        for condition in rule_map['location_conditions']:
            condtions.append(condition)

        if self.rule_conditions_are_met(condtions, entry_point, train_locations) is False:
            return train_locations

        for i in range(len(train_locations)):
            for condition in rule_map['location_conditions']:
                if condition != 'OR':
                    if self.is_condition_met(condition, entry_point, [train_locations[i]]) is True:
                        train_locations.pop(i)
                        return train_locations
        return train_locations

    def determine_entry_time_from_location(self, location_name, train_locations, entry_time):
        readable_l_name = common.find_readable_location(location_name, self.locations_map)
        if readable_l_name == '':
            return entry_time
        for l in train_locations:
            if l['location'] == readable_l_name:
                if 'dep' in l:
                    return l['dep']
                if 'arr' in l:
                    return l['arr']
        return entry_time

