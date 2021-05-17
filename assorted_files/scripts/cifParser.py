from string import capwords

f = open('cif_sample.cif', mode='r')

import_tiploc = False
import_associations = True
import_atoc_schedule = False
current_schedule = {}
i = 0

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
        if import_atoc_schedule is True:
            if line[2:3] == 'D' or line[79:80] == 'C':
                continue

            # TODO filter trains not on right date
            # 'start_date': convert_date(line[9:15]),
            # 'end_date'	: convert_date(line[15:21]),
            # 'days_run'		: line[21:28],
            # 'bank_holiday_running'	: line[28:29],

            # not a train
            train_status = line[29:30].strip()
            if train_status in ['B', 'S', '4', '5']:
                continue

            current_schedule = {'uid': line[3:9].strip(),
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

            # dayno = 0
            # for day in list(db_values['days_run']):
            #     db_values['day' + str(dayno)] = day
            #     dayno += 1

            for value in current_schedule.values():
                if value == '':
                    value = None


    elif line[0:2] == 'BX':  # Basic Schedule Extra Details

        if import_atoc_schedule is True and len(current_schedule) > 0:
            if line[2:3] == 'D' or line[79:80] == 'C':
                continue

            operator_code = line[11:13].strip()

            if operator_code != '':
                current_schedule['operator_code'] = line[11:13]
            else:
                current_schedule['operator_code'] = None


    elif line[0:2] == 'TN':  # Train specific note
        continue

    elif line[0:2] == 'LO':  # Location Origin
        if import_atoc_schedule is True and len(current_schedule) > 0:
            location = {'Tiploc_Code': line[2:9].strip(),
                        # 'tiploc_instance'	: line[9:10],
                        'dep': line[10:15].strip(),
                        # 'public_departure'	: convert_time(line[15:19]),
                        'plat': line[19:22].strip(),
                        'line': line[22:25].strip(),
                        'eng allow': line[25:27].strip(),
                        'pth allow': line[27:29].strip(),
                        'Activity': line[29:41].strip(),
                        'prf allow': line[41:43].strip()}

            for value in location.values():
                if value == '':
                    value = None

            current_schedule['locations'].append(location)


    elif line[0:2] == 'LI':  # Location Intermediate
        if import_atoc_schedule is True and len(current_schedule) > 0:
            location = {'Tiploc_Code': line[2:9].strip(),
                        # 'tiploc_instance'	: line[9:10],
                        'arr': line[10:15].strip(),
                        'dep': line[15:20].strip(),
                        'pass': line[20:25].strip(),
                        'plat': line[33:36].strip(),
                        'line': line[36:39].strip(),
                        'path': line[39:42].strip(),
                        'Activity': line[42:54].strip(),
                        'eng allow': line[54:56].strip(),
                        'pth allow': line[56:58].strip(),
                        'prf allow': line[58:60].strip()}

            for value in location.values():
                if value == '':
                    value = None

            current_schedule['locations'].append(location)

    elif line[0:2] == 'LT':  # Location Terminus
        if import_atoc_schedule is True and len(current_schedule) > 0:
            location = {'Tiploc_Code': line[2:9].strip(),
                        'arr': line[10:15].strip(),
                        'plat': line[19:22].strip(),
                        'path': line[22:25].strip(),
                        'Activity': line[25:37].strip()}

            for value in location.values():
                if value == '':
                    value = None

            current_schedule['locations'].append(location)

            # insert current schedule into DB
            # print(current_schedule)
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
