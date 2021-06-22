from string import capwords
import datetime
from pymongo import MongoClient

DOES_NOT_RUN = 0
RUNS_ON_PREV_DATE = 1
RUNS_ON_DATE = 2
RUNS_ON_BOTH_DATES = 3
ASSOCIATION_DICT = {'JJ': 'trainJoins', 'VV': 'divideRear', 'NP': 'trainBecomes'}

date_of_tt = '181126'
date_of_tt_as_datetime = datetime.datetime(int(f'20{date_of_tt[0:2]}'), int(date_of_tt[2:4]), int(date_of_tt[4:6]))
readable_date_of_tt = "{:%d %B %Y}".format(date_of_tt_as_datetime).replace(' ', '_')

mongo_client = MongoClient('mongodb://localhost:27017/')
mongo_db = mongo_client[readable_date_of_tt]
schedules_on_date_collection = mongo_db['sched_on_day']
schedules_on_previous_date_collection = mongo_db['sched_previous_day']
assoc_on_date_collection = mongo_db['assoc_on_day']
assoc_on_previous_date_collection = mongo_db['assoc_previous_day']


def dates_and_days_apply(date_of_tt_as_int: int, day_of_date: int, start_date: str, end_date: str,
                         days_run: str) -> int:
    if end_date.strip() == '':
        if start_date.strip() == '':
            return DOES_NOT_RUN
        elif int(start_date) == date_of_tt_as_int:
            return RUNS_ON_DATE
        elif int(start_date) == date_of_tt_as_int - 1:
            return RUNS_ON_PREV_DATE
        return DOES_NOT_RUN

    start_after_date = int(start_date) > date_of_tt_as_int
    end_before_previous = int(end_date) < date_of_tt_as_int - 1

    # If date range does not cover either.
    if start_after_date is True or end_before_previous is True:
        return DOES_NOT_RUN

    if days_run.strip() == '':
        # Not sure if we will get this with a start and end present.
        if start_date == end_date:
            if int(start_date) == date_of_tt_as_int:
                return RUNS_ON_DATE
            if int(start_date) == date_of_tt_as_int - 1:
                return RUNS_ON_PREV_DATE
            return DOES_NOT_RUN

    runs_on_day = days_run[day_of_date] == '1'
    runs_on_previous_day = days_run[(day_of_date - 1) % 7] == '1'

    # In range but does not run on either
    if runs_on_day is False and runs_on_previous_day is False:
        return DOES_NOT_RUN

    start_after_previous = int(start_date) > date_of_tt_as_int - 1
    end_before_date = int(end_date) < date_of_tt_as_int

    if runs_on_day is True and runs_on_previous_day is True:
        if start_after_previous is True:
            # must start on date o.w. start_after_date would be True
            return RUNS_ON_DATE
        if end_before_date is True:
            return RUNS_ON_PREV_DATE
        # all date related vars must be false so both days in range
        return RUNS_ON_BOTH_DATES

    if runs_on_previous_day is False:
        if end_before_date is True:
            return DOES_NOT_RUN
        return RUNS_ON_DATE

    if runs_on_day is False:
        if start_after_previous is True:
            return DOES_NOT_RUN
        return RUNS_ON_PREV_DATE

    return DOES_NOT_RUN


def times_cross_midnight(locations: list) -> bool:
    flattened_times = []
    for l in locations:
        if 'arr' in l and l['arr'] != '':
            flattened_times.append(int(l['arr'][0:4]))
        if 'dep' in l and l['dep'] != '':
            flattened_times.append(int(l['dep'][0:4]))

    for i in range(len(flattened_times) - 1):
        if flattened_times[i] > flattened_times[i + 1]:
            return True

    return False


def remove_basic_schedule_from_db(uid: str, start_date: str, date_runs: int, stp_indicator: str):
    if date_runs == RUNS_ON_BOTH_DATES or date_runs == RUNS_ON_PREV_DATE:
        schedules_on_previous_date_collection.delete_one(
            {'uid': uid, 'Start_Date': start_date, 'STP_Indicator': stp_indicator})

    if date_runs == RUNS_ON_BOTH_DATES or date_runs == RUNS_ON_DATE:
        schedules_on_date_collection.delete_one({'uid': uid, 'Start_Date': start_date, 'STP_Indicator': stp_indicator})


def temporarily_cancel_schedule(uid: str, start_date: str, date_runs: int, stp_indicator: str):
    if date_runs == RUNS_ON_BOTH_DATES or date_runs == RUNS_ON_PREV_DATE:
        # Cancel schedule from yesterday
        schedules_on_previous_date_collection.insert_one(
            {'uid': uid, 'Start_Date': start_date, 'STP_Indicator': stp_indicator})

    if date_runs == RUNS_ON_BOTH_DATES or date_runs == RUNS_ON_DATE:
        # Cancel schedule from today
        schedules_on_date_collection.insert_one({'uid': uid, 'Start_Date': start_date, 'STP_Indicator': stp_indicator})


def add_schedule_to_yesterday_db(current_schedule: dict, transaction_type: str):
    add_schedule_to_db(current_schedule, transaction_type, schedules_on_previous_date_collection)


def add_schedule_to_today_db(current_schedule: dict, transaction_type: str):
    add_schedule_to_db(current_schedule, transaction_type, schedules_on_date_collection)


def add_schedule_to_db(current_schedule: dict, transaction_type: str, db):
    if transaction_type == 'R' or current_schedule['STP_Indicator'] == 'O':
        # try to replace existing schedule
        db.find_one_and_replace({'uid': current_schedule['uid'], 'Start_Date': current_schedule['Start_Date'],
                                 'STP_Indicator': current_schedule['STP_Indicator']}, current_schedule, upsert=True)
    else:
        # must be a new one
        db.insert_one(current_schedule)


def remove_assoc_from_db(main_train_uid: str, assoc_train_uid: str, start_date: str, date_runs: int,
                         stp_indicator: str):
    if date_runs == RUNS_ON_BOTH_DATES or date_runs == RUNS_ON_PREV_DATE:
        assoc_on_previous_date_collection.delete_one(
            {'main_train_uid': main_train_uid, 'assoc_train_uid': assoc_train_uid, 'start_date': start_date,
             'STP_Indicator': stp_indicator})

    if date_runs == RUNS_ON_BOTH_DATES or date_runs == RUNS_ON_DATE:
        assoc_on_date_collection.delete_one(
            {'main_train_uid': main_train_uid, 'assoc_train_uid': assoc_train_uid, 'start_date': start_date,
             'STP_Indicator': stp_indicator})


def temporarily_cancel_assoc(main_train_uid: str, assoc_train_uid: str, start_date: str, date_runs: int,
                             stp_indicator: str):
    if date_runs == RUNS_ON_BOTH_DATES or date_runs == RUNS_ON_PREV_DATE:
        assoc_on_previous_date_collection.insert_one(
            {'main_train_uid': main_train_uid, 'assoc_train_uid': assoc_train_uid, 'start_date': start_date,
             'STP_Indicator': stp_indicator})

    if date_runs == RUNS_ON_BOTH_DATES or date_runs == RUNS_ON_DATE:
        assoc_on_date_collection.insert_one(
            {'main_train_uid': main_train_uid, 'assoc_train_uid': assoc_train_uid, 'start_date': start_date,
             'STP_Indicator': stp_indicator})


def add_assoc_to_yesterday_db(assoc_record: dict, transaction_type: str):
    add_assoc_to_db(assoc_record, transaction_type, assoc_on_previous_date_collection)


def add_assoc_to_today_db(assoc_record: dict, transaction_type: str):
    add_assoc_to_db(assoc_record, transaction_type, assoc_on_date_collection)


def add_assoc_to_db(assoc_record: dict, transaction_type: str, db):

    if assoc_record['STP_Indicator'] == 'O':
        if assoc_record['activity'] == '':
            # find original and input the activity
            current_record = db.find_one({'main_train_uid': assoc_record['main_train_uid'],
                                     'assoc_train_uid': assoc_record['assoc_train_uid'],
                                     'start_date': assoc_record['start_date'],
                                     'STP_Indicator': 'P'})

            if current_record is not None:
                assoc_record['activity'] = current_record['activity']
                db.find_one_and_replace({'main_train_uid': assoc_record['main_train_uid'],
                                         'assoc_train_uid': assoc_record['assoc_train_uid'],
                                         'start_date': assoc_record['start_date'],
                                         'STP_Indicator': assoc_record['STP_Indicator']}, assoc_record, upsert=True)
        else:
            db.find_one_and_replace({'main_train_uid': assoc_record['main_train_uid'],
                                     'assoc_train_uid': assoc_record['assoc_train_uid'],
                                     'start_date': assoc_record['start_date'],
                                     'STP_Indicator': assoc_record['STP_Indicator']}, assoc_record, upsert=True)

    elif transaction_type == 'R':
        db.find_one_and_replace({'main_train_uid': assoc_record['main_train_uid'],
                                 'assoc_train_uid': assoc_record['assoc_train_uid'],
                                 'start_date': assoc_record['start_date'],
                                 'STP_Indicator': assoc_record['STP_Indicator']}, assoc_record, upsert=True)
    else:
        # must be a new one
        db.insert_one(assoc_record)


def parse_cif_file(filename: str, date_of_tt: str, **kwargs):
    f = open(filename, mode='r')

    date_of_tt_as_int = int(date_of_tt)
    day_of_date = date_of_tt_as_datetime.weekday()

    import_tiploc = 'import_tiploc' in kwargs and kwargs['import_tiploc'] is True
    import_associations = 'import_associations' in kwargs and kwargs['import_associations'] is True
    import_atoc_schedule = 'import_full_atoc_schedule' in kwargs and kwargs['import_full_atoc_schedule'] is True
    is_update = 'import_update_atoc_schedule' in kwargs and kwargs['import_update_atoc_schedule'] is True

    if is_update is True:
        import_atoc_schedule = True

    if sum([import_tiploc, import_associations, import_atoc_schedule]) != 1:
        raise Exception('Wrong boolean args')

    current_schedule = {}
    date_runs = DOES_NOT_RUN
    i = 0
    transaction_type = ''
    stp_indicator = ''

    for line in f:
        if line[0:2] == 'HD':  # Header record
            print(line)

        elif line[0:2] == 'TI':  # TIPLOC Insert
            if import_tiploc is True:
                db_values = {'tiploc': line[2:9].strip(),
                             'tps_description': capwords(line[18:44]).strip()}

                for value in db_values.values():
                    if value == '':
                        value = None

                # Insert into db
                print(db_values)

        elif line[0:2] == 'TA':  # TIPLOC Delete
            continue

        elif line[0:2] == 'TD':  # TIPLOC Delete
            continue

        elif line[0:2] == 'AA':  # Associations
            if import_associations is True:
                start_date = line[15:21]
                end_date = line[21:27]
                days_run = line[27:34]
                date_runs = dates_and_days_apply(date_of_tt_as_int, day_of_date, start_date, end_date, days_run)

                if date_runs == DOES_NOT_RUN:
                    continue

                transaction_type = line[2:3].strip()
                stp_indicator = line[79:80].strip()
                main_train_uid = line[3:9].strip()
                assoc_train_uid = line[9:15].strip()

                if transaction_type == 'D':
                    if is_update is False:
                        continue
                    remove_assoc_from_db(main_train_uid, assoc_train_uid, start_date, date_runs, stp_indicator)

                if stp_indicator == 'C':
                    if is_update is False:
                        continue
                    temporarily_cancel_assoc(main_train_uid, assoc_train_uid, start_date, date_runs, stp_indicator)

                db_values = {'main_train_uid': main_train_uid,
                             'assoc_train_uid': assoc_train_uid,
                             'start_date': line[15:21].strip(),
                             'end_date': line[21:27].strip(),
                             'days_run': line[27:34].strip(),
                             'activity': line[34:36].strip(),
                             'date_indicator': line[36:37].strip(),
                             'location': line[37:44].strip(),
                             'base_location_suffix': line[44:45].strip(),
                             'assoc_location_suffix': line[45:46].strip(),
                             'STP_Indicator': stp_indicator}

                if date_runs == RUNS_ON_PREV_DATE or date_runs == RUNS_ON_BOTH_DATES:
                    add_assoc_to_yesterday_db(db_values, transaction_type)

                if date_runs == RUNS_ON_BOTH_DATES or date_runs == RUNS_ON_DATE:
                    add_assoc_to_today_db(db_values, transaction_type)

        elif line[0:2] == 'BS':  # Basic Schedule
            if import_atoc_schedule is True:

                # Don't want to do it if not applicable to day
                start_date = line[9:15]
                end_date = line[15:21]
                days_run = line[21:28]
                date_runs = dates_and_days_apply(date_of_tt_as_int, day_of_date, start_date, end_date, days_run)

                if date_runs == DOES_NOT_RUN:
                    continue

                transaction_type = line[2:3]
                stp_indicator = line[79:80]
                uid = line[3:9].strip()

                # Handle record deletion first because info can be incomplete
                if transaction_type == 'D':
                    if is_update is False:
                        continue
                    # Update so remove from db
                    remove_basic_schedule_from_db(uid, start_date, date_runs, stp_indicator)

                if stp_indicator == 'C':
                    if is_update is False:
                        continue
                    # Update so we want to move original sched to cancelled
                    temporarily_cancel_schedule(uid, start_date, date_runs, stp_indicator)

                # not a train
                train_status = line[29:30].strip()
                if train_status in ['B', 'S', '4', '5']:
                    continue

                current_schedule = {'uid': uid,
                                    'Start_Date': start_date,
                                    'STP_Indicator': stp_indicator,
                                    'Train_Status': train_status,
                                    'Train_Category': line[30:32].strip(),
                                    'headcode': line[32:36].strip(),
                                    'Portion_Id': line[49:50].strip(),
                                    'Power_Type': line[50:53].strip(),
                                    'Timing_Load': line[53:57].strip(),
                                    'max_speed': line[57:60].strip(),
                                    'Operating_Characteristics': line[60:66].strip(),
                                    'locations': []}

        elif line[0:2] == 'BX':  # Basic Schedule Extra Details
            if date_runs > 0 and import_atoc_schedule is True and len(current_schedule) > 0:

                operator_code = line[11:13].strip()

                if operator_code != '':
                    current_schedule['operator_code'] = line[11:13]
                else:
                    current_schedule['operator_code'] = ''

        elif line[0:2] == 'TN':  # Train specific note
            continue

        elif line[0:2] == 'LO':  # Location Origin
            if date_runs > 0 and import_atoc_schedule is True and len(current_schedule) > 0:
                location = {'location': line[2:9].strip(),
                            'Location_Instance': line[9:10].strip(),
                            'dep': line[10:15].strip().replace('H', '.5'),
                            'plat': line[19:22].strip(),
                            'line': line[22:25].strip(),
                            'eng allow': line[25:27].strip().replace('H', '.5'),
                            'pth allow': line[27:29].strip().replace('H', '.5'),
                            'Activities': line[29:41].strip(),
                            'prf allow': line[41:43].strip().replace('H', '.5')}

                current_schedule['locations'].append(location)

        elif line[0:2] == 'LI':  # Location Intermediate
            if date_runs > 0 and import_atoc_schedule is True and len(current_schedule) > 0:
                arr = line[10:15].strip().replace('H', '.5')
                dep = line[15:20].strip().replace('H', '.5')
                _pass = line[20:25].strip().replace('H', '.5')
                if (arr == '' or dep == '') and _pass != '':
                    dep = _pass
                    location = {'location': line[2:9].strip(),
                                'Location_Instance': line[9:10],
                                'arr': arr,
                                'dep': dep,
                                'plat': line[33:36].strip(),
                                'line': line[36:39].strip(),
                                'path': line[39:42].strip(),
                                'Activities': line[42:54].strip(),
                                'eng allow': line[54:56].strip().replace('H', '.5'),
                                'pth allow': line[56:58].strip().replace('H', '.5'),
                                'prf allow': line[58:60].strip().replace('H', '.5'),
                                'is_pass_time': '-1'}
                else:
                    location = {'location': line[2:9].strip(),
                                'Location_Instance': line[9:10],
                                'arr': arr,
                                'dep': dep,
                                'plat': line[33:36].strip(),
                                'line': line[36:39].strip(),
                                'path': line[39:42].strip(),
                                'Activities': line[42:54].strip(),
                                'eng allow': line[54:56].strip().replace('H', '.5'),
                                'pth allow': line[56:58].strip().replace('H', '.5'),
                                'prf allow': line[58:60].strip().replace('H', '.5')}

                current_schedule['locations'].append(location)

        elif line[0:2] == 'LT':  # Location Terminus
            if date_runs > 0 and import_atoc_schedule is True and len(current_schedule) > 0:
                location = {'location': line[2:9].strip(),
                            'Location_Instance': line[9:10],
                            'arr': line[10:15].strip().replace('H', '.5'),
                            'plat': line[19:22].strip(),
                            'path': line[22:25].strip(),
                            'Activities': line[25:37].strip()}

                current_schedule['locations'].append(location)

                if date_runs == RUNS_ON_PREV_DATE or date_runs == RUNS_ON_BOTH_DATES:
                    if times_cross_midnight(current_schedule['locations']) is True:
                        add_schedule_to_yesterday_db(current_schedule, transaction_type)

                if date_runs == RUNS_ON_BOTH_DATES or date_runs == RUNS_ON_DATE:
                    add_schedule_to_today_db(current_schedule, transaction_type)

                current_schedule = {}

        elif line[0:2] == 'C  ':  # Change en route
            continue

        elif line[0:2] == 'L  ':  # Location Note
            continue

        elif line[0:2] == 'Z  ':  # Trailer Record
            continue

        i += 1
        if i % 1000 == 0:
            print(f"Imported to line {i}")
    f.close()

def apply_associations_to_schedules():
    # For reference
    a = {'main_train_uid': main_train_uid,
                             'assoc_train_uid': assoc_train_uid,
                             'start_date': line[15:21].strip(),
                             'end_date': line[21:27].strip(),
                             'days_run': line[27:34].strip(),
                             'activity': line[34:36].strip(),
                             'date_indicator': line[36:37].strip(),
                             'location': line[37:44].strip(),
                             'base_location_suffix': line[44:45].strip(),
                             'assoc_location_suffix': line[45:46].strip(),
                             'STP_Indicator': stp_indicator}


    # TODO implement this

    for assoc in assoc_on_date_collection.find():
        # check activity type
        activity = assoc['activity']
        if activity == 'JJ':
            # need to find both schedules
            main_uid = assoc['main_train_uid']
            assoc_uid = assoc['assoc_train_uid']

            main_train = find_sched_in_current(main_uid)
            if main_train is not None:
                assoc_train = find_sched_in_current(assoc_uid)

            schedules_on_date_collection
            schedules_on_previous_date_collection
            # if we can find both then will disregard

            # now update schedules

        if activity == 'VV':
            #

        if activity == 'NP':

if __name__ == "__main__":
    parse_cif_file('23-full.cif', date_of_tt, import_full_atoc_schedule=True)
    parse_cif_file('23-update.cif', date_of_tt, import_update_atoc_schedule=True)
    parse_cif_file('24-update.cif', date_of_tt, import_update_atoc_schedule=True)
    parse_cif_file('25-update.cif', date_of_tt, import_update_atoc_schedule=True)
