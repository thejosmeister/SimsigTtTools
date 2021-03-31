"""
For executing custom (and some general) logic on sim locations for a train.
"""
import yaml


class CustomLogicExecutor:

    def __init__(self, sim_id: str, locations_map: dict, entry_points_map: dict):
        self.locations_map = locations_map
        self.entry_points_map = entry_points_map

        # get custom specs
        custom_specs_location = f'spec_files/sim_custom_location_logic/{sim_id}.yaml'
        with open(custom_specs_location, 'r') as stream:
            self.custom_specs = yaml.safe_load(stream)

        # May instantiate dbs here in future

    def perform_custom_logic(self, train_locations: list, potential_entry: str) -> list:
        """
        :param train_locations: prospective train locations to undergo logic.
        :param potential_entry: the potential entry point for the train
        :return: [ entry_point?, entry_time?, tt_template, location_list ]
        """

        # Look to see if entry point has custom logic
        if potential_entry in self.custom_specs['entry_point_rules']:
            entry_point, entry_time, tt_template, train_locations = self.apply_custom_entry_logic(train_locations,
                                                                                                  potential_entry)
        # If not then apply default

        # For each location in custom logic apply custom rules

    def apply_custom_entry_logic(self, train_locations, potential_entry):
        rules_for_entry = self.custom_specs['entry_point_rules'][potential_entry]

        for rule in rules_for_entry:
            if rule == 'list_to_delete_if_before':
                entry_point, entry_time, tt_template, new_locations = self.list_to_delete_if_before(
                    rules_for_entry[rule], potential_entry, train_locations)

        return [None, None, None, new_locations]

    def list_to_delete_if_before(self, list_to_delete, potential_entry, train_locations):
        entry_location, entry_time = self.get_entry_location_and_time(potential_entry, train_locations)

        if entry_location is None:
            # If we cant find anything then bail out with a default
            return [potential_entry, train_locations[0]['dep'],
                    'templates/timetables/defaultTimetableWithEntryPoint.txt', train_locations]
        for location in list_to_delete:
            if self.x_before_y( location, entry_location, train_locations) is True:

        pass

    def get_entry_location_and_time(self, potential_entry, train_locations):
        tiploc_for_entry = self.entry_points_map[potential_entry][-1]
        readable_entry_name = self.locations_map[tiploc_for_entry][0]

        entry_location = self.get_location_in_list(readable_entry_name, train_locations)
        if entry_location is not None:
            if 'dep' in entry_location:
                return [entry_location['location'], entry_location['dep']]
            return [entry_location['location'], entry_location['arr']]

        return [None, None]

    def get_location_in_list(self, readable_entry_name, train_locations):
        loc_list = list(filter(lambda x: x['location'] == readable_entry_name, train_locations))
        if len(loc_list) == 1:
            return loc_list[0]
        return None
