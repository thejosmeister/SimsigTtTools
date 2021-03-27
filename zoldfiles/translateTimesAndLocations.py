"""
Some bits I wrote to transform the information in the json locations files to values that Simsig recognises
"""
import ast
import math
import re


def convert_time_to_secs(time: str) -> int:
    """
    Converts a time string in the format hhmm to seconds past midnight
    :param time: Time string, format hhmm
    :return: The time as seconds from midnight
    """
    match = re.match("(\\d{2})(\\d{2})(?:\\.(\\d+))?", time)
    hours = int(match.group(1))
    mins = int(match.group(2))
    if len(time) > 4:
        secs = math.floor(60 * float('0.' + match.group(3)))
    else:
        secs = 0

    return (3600 * hours) + (60 * mins) + secs


def convert_sec_to_time(time: int) -> str:
    """
    Converts seconds past midnight to a time string in the format hhmm.
    :param time: Seconds past midnight
    :return:
    """
    hours = math.floor(time / 3600)
    mins = math.floor((time - (hours * 3600))/60)
    secs = math.floor(time - (hours * 3600) - (mins * 60))

    if secs > 0:
        return f"{hours:02d}{mins:02d}." + str(round(secs/60, 1))[2:3]
    else:
        return f"{hours:02d}{mins:02d}"


# Will create a new location list which only contains sim locations with the relevant location code.
def only_add_locations_in_sim(sorted_locations: list, tiploc_dict: dict, origin: str) -> list:
    out = []
    entry_time = ''
    for l in sorted_locations:
        for t in tiploc_dict.keys():
            if l['location'] in tiploc_dict[t]:
                # isOrigin is used to tell whether the location needs a pass time flag.
                if origin == l['location']:
                    l['isOrigin'] = 'yes'
                out.append(l)
            elif 'Entry' in l['location']:
                # Used as a way to specify entry time in original location list.
                entry_time = l['dep']

    return [out, entry_time]


# Will sub in TIPLOC codes for locations in the sim
def sub_in_tiploc(sorted_locations: list, tiploc_dict: dict) -> list:
    out = []
    for l in sorted_locations:
        for t in tiploc_dict.keys():
            if l['location'] in tiploc_dict[t]:
                l['location'] = str(t)
                out.append(l)

    return out


# Used in sorting lambda.
def return_value(inp: dict):
    if 'dep' in inp:
        return inp['dep']
    elif 'arr' in inp:
        return inp['arr']


def produce_train_locations(location_template_filename: str) -> list:
    """
    Takes a file containing list of json locations for a train and outputs it to a python list of dicts.
    :param location_template_filename: json list train TT.
    :return: json list of locations of a train on the sim.
    """
    f = open(location_template_filename, "r")
    list_of_locations = ast.literal_eval(f.read())
    f.close()

    for l in list_of_locations:
        if 'dep' in l:
            if l['dep'] == '':
                l.pop('dep', None)
        if 'arr' in l:
            if l['arr'] == '':
                l.pop('arr', None)

    return list_of_locations


def produce_dict_with_times_and_locations(list_of_locations: list, tiploc_dict: dict) -> list:
    """
    Takes a list of json locations for a train and outputs in a list:
     - origin time in hhmm format
     - origin name (not TIPLOC)
     - the entry time of the train into the sim according to 'Entry' being the location field.
     - destination time in hhmm format
     - destination name (not TIPLOC)
     - json list of locations of a train on the sim, time is in seconds past midnight and location names are NOT TIPLOC
    :param list_of_locations: list of train TT maps.
    :param tiploc_dict: Map of TIPLOC codes to place names.
    :return: Specified above.
    """

    for l in list_of_locations:
        if 'dep' in l:
            l['dep'] = convert_time_to_secs(l['dep'])
        if 'arr' in l:
            l['arr'] = convert_time_to_secs(l['arr'])

    sorted_locations = sorted(list_of_locations, key=lambda x: return_value(x))
    origin = sorted_locations[0]['location']
    origin_time = convert_sec_to_time(sorted_locations[0]['dep'])
    dest = sorted_locations[-1]['location']
    dest_time = convert_sec_to_time(sorted_locations[-1]['arr'])
    [locations_on_sim, entry_time] = only_add_locations_in_sim(sorted_locations, tiploc_dict, origin)

    return [origin_time, origin, entry_time, dest_time, dest, locations_on_sim]


