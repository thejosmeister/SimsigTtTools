"""
For executing custom (and some general) logic on sim locations for a train.
"""
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

    def Perform_Custom_Logic(self, train_locations: list, potential_entry: str) -> list:
        """
        :param train_locations: prospective train locations to undergo logic.
        :param potential_entry: the potential entry point for the train
        :return: [ entry_point?, entry_time?, tt_template, location_list ]
        """

        # Look to see if entry point has custom logic
        entry_location, entry_time = self.get_entry_location_and_time(potential_entry, train_locations)
        if potential_entry in self.custom_specs['entry_point_rules']:
            entry_point, entry_time, \
            tt_template, train_locations = self.apply_custom_entry_logic(train_locations, entry_location, entry_time,
                                                                         potential_entry)
        # If not then apply default
        else:
            entry_point, entry_time, \
            tt_template, train_locations = self.apply_generic_entry_logic(train_locations, entry_location, entry_time,
                                                                          potential_entry)

        # For each location in custom logic apply custom rules
        train_locations = self.apply_location_logic(train_locations)


        return [entry_point, entry_time, tt_template, train_locations]

    def apply_custom_entry_logic(self, train_locations, entry_location, entry_time, potential_entry):
        rules_for_entry = self.custom_specs['entry_point_rules'][potential_entry]

        for rule in rules_for_entry:
            if rule == 'list_to_delete_if_before':
                train_locations = self.list_to_delete_if_before(
                    rules_for_entry[rule], entry_location, entry_time, train_locations)
                return self.apply_generic_entry_logic(train_locations, entry_location, entry_time, potential_entry)
            if rule == 'if_later_location_matching':
                return self.if_later_location_matching(rules_for_entry[rule], entry_location, entry_time, train_locations ,potential_entry)

        return None

    def list_to_delete_if_before(self, list_to_delete, entry_location, entry_time, train_locations):
        """
        Will delete any of these found before the entry point location.
        """
        if entry_location is None:
            return train_locations

        for location in list_to_delete:
            if self.x_before_y(location, entry_location, train_locations) is True:
                train_locations = self.remove_location(location, train_locations)

        return train_locations

    def get_entry_location_and_time(self, potential_entry, train_locations):
        """
        Returns an associated entry location name and time if found.
        """
        tiploc_for_entry = self.entry_points_map[potential_entry][-1]
        readable_entry_name = common.find_readable_location(tiploc_for_entry, self.locations_map)

        entry_location = self.get_entry_location_in_list(readable_entry_name, train_locations)
        if entry_location is not None:
            if 'dep' in entry_location:
                return [entry_location['location'], entry_location['dep']]
            return [entry_location['location'], entry_location['arr']]

        return [None, None]

    def get_entry_location_in_list(self, readable_entry_name, train_locations):
        """
        Returns the whole location, not just the name.
        """
        loc_list = list(filter(lambda x: x['location'] == readable_entry_name, train_locations))
        if len(loc_list) == 1:
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

    def remove_location(self, location_to_remove, train_locations):
        standard_location_to_remove = common.find_readable_location(location_to_remove, self.locations_map)
        return list(filter(lambda x: x['location'] != standard_location_to_remove, train_locations))

    def apply_generic_entry_logic(self, train_locations, entry_location, entry_time, potential_entry):
        """
        If potential entry is 1st location then capture dep time as entry time and delete location.
        If potential entry is not 1st location (implicitly no custom) then assume train starts on sim.
        If potential entry does not match to any locations then assume at start and take nominal entry time from 1st location.
        If no potential entry then assume starts on sim.
        """

        # If we cant find anything then bail out with a default
        if entry_location is None and potential_entry is not None:
            return [potential_entry, train_locations[0]['dep'],
                    'templates/timetables/defaultTimetableWithEntryPoint.txt', train_locations]

        # If entry is first location then we delete first location and are done.
        if train_locations[0]['location'] == entry_location:
            train_locations = self.remove_location(entry_location, train_locations)
            return [potential_entry, entry_time,
                    'templates/timetables/defaultTimetableWithEntryPoint.txt', train_locations]

        # Assume starts on sim.
        return [None, None, 'templates/timetables/defaultTimetableNoEP.txt', train_locations]

    def if_later_location_matching(self, rule_root, entry_location, entry_time, train_locations, potential_entry):
        # TODO implement this
        return self.apply_generic_entry_logic(train_locations, entry_location, entry_time, potential_entry)

    def apply_location_logic(self, train_locations):
        return train_locations


