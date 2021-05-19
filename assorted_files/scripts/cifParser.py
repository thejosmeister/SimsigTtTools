from string import capwords
import datetime
from pymongo import MongoClient

DOES_NOT_RUN = 0
RUNS_ON_PREV_DATE = 1
RUNS_ON_DATE = 2
RUNS_ON_BOTH_DATES = 3

mongo_client = MongoClient('db_url')
mongo_db = mongo_client['date_of_db']
schedules_on_date_collection = mongo_db['date_of_db']
schedules_on_previous_date_collection = mongo_db['date_before_of_db']

def dates_and_days_apply(date_of_tt_as_int: int, day_of_date: int, start_date: str, end_date: str, days_run: str) -> int:

    start_after_date = int(start_date) > date_of_tt_as_int
    end_before_previous = int(end_date) < date_of_tt_as_int - 1

    # If date range does not cover either.
    if start_after_date is True or end_before_previous is True:
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
        if flattened_times[i] > flattened_times[i+1]:
            return True

    return False


def remove_basic_schedule_from_db(uid: str, date_runs: int, stp_indicator: str):

    if date_runs == RUNS_ON_BOTH_DATES or date_runs == RUNS_ON_PREV_DATE:
        if stp_indicator == 'C':
            # Uncancel schedule from yesterday
            print('Uncancel schedule from yesterday')
        else:
            # Remove from yesterday
            print('Remove from yesterday')
    if date_runs == RUNS_ON_BOTH_DATES or date_runs == RUNS_ON_DATE:
        if stp_indicator == 'C':
            # Uncancel schedule from today
            print('Uncancel schedule from today')
        else:
            # Remove from today
            print('Remove from today')

    pass


def temporarily_cancel_schedule(uid, date_runs):
    # find sched in relevant db(s) and insert cancelled flag
    if date_runs == RUNS_ON_BOTH_DATES or date_runs == RUNS_ON_PREV_DATE:
        # Cancel schedule from yesterday
        print('Cancel schedule from yesterday')
    if date_runs == RUNS_ON_BOTH_DATES or date_runs == RUNS_ON_DATE:
        # Cancel schedule from today
        print('Cancel schedule from today')
    pass


def add_schedule_to_yesterday_db(current_schedule: dict, transaction_type: str, stp_indicator: str):
    add_schedule_to_db(current_schedule, transaction_type, stp_indicator, schedules_on_previous_date_collection)


def add_schedule_to_today_db(current_schedule: dict, transaction_type: str, stp_indicator: str):
    add_schedule_to_db(current_schedule, transaction_type, stp_indicator, schedules_on_date_collection)


def add_schedule_to_db(current_schedule: dict, transaction_type: str, stp_indicator: str, db):
    if stp_indicator == 'O':
        if transaction_type == 'R':
            # replace the overlay that should be there
            print()
        else:
            # change _id to suffix with O for original and then insert this one in place
            print()
    else:
        if transaction_type == 'R':
            # replace sched that should be there
            print()
        else:
            # add new schedule
            db.insert_one()
    pass


def parse_cif_file(filename: str, date_of_tt: str, **kwargs):
    f = open(filename, mode='r')

    date_of_tt_as_int = int(date_of_tt)
    day_of_date = datetime.datetime(int(f'20{date_of_tt[0:2]}'), int(date_of_tt[2:4]), int(date_of_tt[4:6]))

    import_tiploc = 'import_tiploc' in kwargs and kwargs['import_tiploc'] is True
    import_associations = 'import_associations' in kwargs and kwargs['import_associations'] is True
    import_full_atoc_schedule = 'import_full_atoc_schedule' in kwargs and kwargs['import_full_atoc_schedule'] is True
    import_update_atoc_schedule = 'import_update_atoc_schedule' in kwargs and kwargs['import_update_atoc_schedule'] is True

    if sum([import_tiploc, import_associations, import_full_atoc_schedule, import_update_atoc_schedule]) != 1:
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
                # Only want ones that apply to our specific day so any deletions or ones on the wrong day are not needed.
                transaction_type = line[2:3].strip()
                stp_indicator = line[79:80].strip()
                if transaction_type == 'D' or stp_indicator == 'C':
                    continue

                # TODO date filtering
                # TODO day filtering

                db_values = {'transaction_type': transaction_type,
                             'main_train_uid': line[3:9].strip(),
                             'assoc_train_uid': line[9:15].strip(),
                             'start_date': line[15:21].strip(),
                             'end_date': line[21:27].strip(),
                             'days_run': line[27:34].strip(),
                             'category': line[34:36].strip(),
                             'date_indicator': line[36:37].strip(),
                             'location': line[37:44].strip(),
                             'base_location_suffix': line[44:45].strip(),
                             'assoc_location_suffix': line[45:46].strip(),
                             'type': line[46:47].strip(),
                             'stp_indicator': stp_indicator}

                # dayno = 0
                # for day in list(db_values['days_run']):
                #     db_values['day' + str(dayno)] = day
                #     dayno += 1

                for value in db_values.values():
                    if value == '':
                        value = None

                # Insert into db
                print(db_values)

        elif line[0:2] == 'BS':  # Basic Schedule
            if import_full_atoc_schedule is True or import_update_atoc_schedule is True:

                # Don't want to do it if not applicable to day
                date_runs = dates_and_days_apply(date_of_tt_as_int, day_of_date, line[9:15], line[15:21], line[21:28])
                if date_runs == 0:
                    continue

                transaction_type = line[2:3]
                stp_indicator = line[79:80]
                uid = line[3:9].strip()

                if transaction_type == 'D':
                    if import_full_atoc_schedule is True:
                        continue
                    # Update so remove from db
                    remove_basic_schedule_from_db(uid, date_runs, stp_indicator)

                if stp_indicator == 'C':
                    if import_full_atoc_schedule is True:
                        continue
                    # Update so we want to move original sched to cancelled
                    temporarily_cancel_schedule(uid, date_runs)

                # not a train
                train_status = line[29:30].strip()
                if train_status in ['B', 'S', '4', '5']:
                    continue

                current_schedule = {'uid': uid,
                                    'train_status': train_status,
                                    'Train_Category': line[30:32].strip(),
                                    'headcode': line[32:36].strip(),
                                    'Portion_Id': line[49:50].strip(),
                                    'Power_Type': line[50:53].strip(),
                                    'Timing_Load': line[53:57].strip(),
                                    'speed': line[57:60].strip(),
                                    'Operating_Characteristics': line[60:66].strip(),
                                    # TODO check if needed.
                                    # 'service_branding'	: line[74:78],
                                    # 'stp_indicator'	: line[79:80]
                                    'locations': []}

        elif line[0:2] == 'BX':  # Basic Schedule Extra Details
            if date_runs > 0 and (import_full_atoc_schedule is True or import_update_atoc_schedule is True) and len(current_schedule) > 0:

                operator_code = line[11:13].strip()

                if operator_code != '':
                    current_schedule['operator_code'] = line[11:13]
                else:
                    current_schedule['operator_code'] = ''

        elif line[0:2] == 'TN':  # Train specific note
            continue

        elif line[0:2] == 'LO':  # Location Origin
            if date_runs > 0 and (import_full_atoc_schedule is True or import_update_atoc_schedule is True) and len(current_schedule) > 0:
                location = {'Tiploc_Code': line[2:9].strip(),
                            # 'tiploc_instance'	: line[9:10],
                            'dep': line[10:15].strip(),
                            'plat': line[19:22].strip(),
                            'line': line[22:25].strip(),
                            'eng allow': line[25:27].strip(),
                            'pth allow': line[27:29].strip(),
                            'Activity': line[29:41].strip(),
                            'prf allow': line[41:43].strip()}

                current_schedule['locations'].append(location)


        elif line[0:2] == 'LI':  # Location Intermediate
            if date_runs > 0 and (import_full_atoc_schedule is True or import_update_atoc_schedule is True) and len(current_schedule) > 0:
                arr = line[10:15].strip()
                dep = line[15:20].strip()
                _pass = line[20:25].strip()
                if (arr == '' or dep == '') and _pass != '':
                    dep = _pass
                    location = {'Tiploc_Code': line[2:9].strip(),
                                # 'tiploc_instance'	: line[9:10],
                                'arr': arr,
                                'dep': dep,
                                'plat': line[33:36].strip(),
                                'line': line[36:39].strip(),
                                'path': line[39:42].strip(),
                                'Activity': line[42:54].strip(),
                                'eng allow': line[54:56].strip(),
                                'pth allow': line[56:58].strip(),
                                'prf allow': line[58:60].strip(),
                                'is_pass_time': '-1' }
                else:
                    location = {'Tiploc_Code': line[2:9].strip(),
                                # 'tiploc_instance'	: line[9:10],
                                'arr': arr,
                                'dep': dep,
                                'plat': line[33:36].strip(),
                                'line': line[36:39].strip(),
                                'path': line[39:42].strip(),
                                'Activity': line[42:54].strip(),
                                'eng allow': line[54:56].strip(),
                                'pth allow': line[56:58].strip(),
                                'prf allow': line[58:60].strip()}

                current_schedule['locations'].append(location)

        elif line[0:2] == 'LT':  # Location Terminus
            if date_runs > 0 and (import_full_atoc_schedule is True or import_update_atoc_schedule is True) and len(current_schedule) > 0:
                location = {'Tiploc_Code': line[2:9].strip(),
                            'arr': line[10:15].strip(),
                            'plat': line[19:22].strip(),
                            'path': line[22:25].strip(),
                            'Activity': line[25:37].strip()}

                current_schedule['locations'].append(location)

                if date_runs == RUNS_ON_PREV_DATE or date_runs == RUNS_ON_BOTH_DATES:
                    if times_cross_midnight(current_schedule['locations']) is True:
                            add_schedule_to_yesterday_db(current_schedule, transaction_type, stp_indicator)

                if date_runs == RUNS_ON_BOTH_DATES or date_runs == RUNS_ON_DATE:
                    add_schedule_to_today_db(current_schedule, transaction_type, stp_indicator)

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
