from dbClient import *


def modify_times():
    traindb = TrainTtDb('swindid_diversions_feb_21')

    traindb.modify_tt_time('1H25', '-PT3M')
    traindb.modify_tt_time('1H28', '-PT3M')
    traindb.modify_tt_time('1H31', '-PT3M')


def test_method():
    db = TrainTtDb('Swindon_A_&_B_IECC_-_SWINDID_130220')
    TT = Query()
    Location = Query()
    results = db.db.search(TT.locations.any(Location.location == 'Didcot North Jn'))

    new_r = []
    for r in results:
        time = [x for x in r['locations'] if x['location'] == 'Didcot North Jn' ][0]['dep']
        new_r.append({'headcode': r['headcode'], 'description': r['description'], 'time': time})

    new_r = sorted(new_r, key=lambda x: float(x['time']))

    [print(r['headcode'] + ' ' + r['description'] + ' ' + r['time']) for r in new_r]

    print('***************************************************************************')


    db = TrainTtDb('Swindon_February_2021')
    TT = Query()
    Location = Query()
    results = db.db.search(TT.locations.any(Location.location == 'Didcot North Jn') & TT.headcode.matches('^((0|4|5|6|7).)\\d{2}$'))

    new_r = []
    for r in results:
        time = [x for x in r['locations'] if x['location'] == 'Didcot North Jn' ][0]['dep']
        new_r.append({'headcode': r['headcode'], 'description': r['origin_time'] + ' ' + r['origin_name'] + ' - ' + r['destination_name'], 'time': time})

    new_r = sorted(new_r, key=lambda x: float(x['time']))

    [print(r['headcode'] + ' ' + r['description'] + ' ' + r['time']) for r in new_r]

test_method()

def different_method():
    db = TrainTtDb('Swindon_February_2021')
    TT = Query()
    results = db.db.search(TT.headcode.matches('^((0|4|5|6|7).)\\d{2}$'))

    new_r = []
    for r in results:
        new_r.append({'headcode': r['headcode'],
                      'description': r['origin_time'] + ' ' + r['origin_name'] + ' - ' + r['destination_name']})

    [print(r['headcode'] + ' ' + r['description']) for r in new_r]


def transfer_from_1_to_another():
    db_21 = TrainTtDb('Swindon_February_2021')
    db_20 = TrainTtDb('Swindon_A_&_B_IECC_-_SWINDID_130220')
    new_db = TrainTtDb('swindid_diversions_feb_21')

    hc_from_21 = ['4M19']
    hc_from_20 = ['4M52']

    for hc in hc_from_20:
        record = db_20.db.search(Query().headcode == hc)[0]
        if not new_db.is_headcode_present(hc):
            print(record['headcode'] + ' * ' + record['origin_time'] + ' * ' + record['origin_name'] + ' * ' + record['destination_name'] + ' * ' + record['category'])
            desc = input('change above description?')
            if desc != 'n':
                parts = desc.split(' * ')
                record['headcode'] = parts[0]
                record['uid'] = record['headcode']
                record['origin_time'] = parts[1]
                record['origin_name'] = parts[2]
                record['destination_name'] = parts[3]
                record['category'] = parts[4]
                record['description'] = record['origin_time'] + ' ' + record['origin_name'] + ' - ' + record['destination_name'] + ' ' + record['category']
            else:
                record['uid'] = record['headcode']

            new_db.add_tt(record)
        else:
            print(hc + ' is already there')

        print(' ')


    for hc in hc_from_21:
        record = db_21.db.search(Query().headcode == hc)[0]
        if not new_db.is_headcode_present(hc):
            print(record['headcode'] + ' * ' + record['origin_time'] + ' * ' + record['origin_name'] + ' * ' + record[
                'destination_name'] + ' * ' + record['category'])
            desc = input('change above description?')
            if desc != 'n':
                parts = desc.split(' * ')
                record['headcode'] = parts[0]
                record['uid'] = record['headcode']
                record['origin_time'] = parts[1]
                record['origin_name'] = parts[2]
                record['destination_name'] = parts[3]
                record['category'] = parts[4]
                record['description'] = record['origin_time'] + ' ' + record['origin_name'] + ' - ' + record[
                    'destination_name'] + ' ' + record['category']
            else:
                new_cat = input('please enter new cat:')
                record['uid'] = record['headcode']
                record['category'] = new_cat
                record['description'] = record['origin_time'] + ' ' + record['origin_name'] + ' - ' + record[
                    'destination_name'] + ' ' + record['category']

            new_db.add_tt(record)

        else:
            print(hc + ' is already there')

        print(' ')


def diag_stock():
    traindb = TrainTtDb('swindid_diversions_feb_21')
    d1 = ['1A01', '1H04', '1A14', '1H12', '1A22', '1H20', '1A30', '1H31']
    d2 = ['1A04', '1H06', '1A18', '1H16', '1A26', '1H25', '1A37']
    d3 = ['1L01', '1B05', '1L18', '1B19', '1L32']
    d4 = ['1H02', '1A12', '1H10', '1A20', '1H18', '1A28', '1H28', '1A40']
    d5 = ['1B03', '1L16', '1B17', '1L30', '1B35']
    d6 = ['1L04', '1B07', '1L20', '1B21', '1L34']
    d7 = ['1A07', '1H08']
    d8 = ['1L08', '1B09', '1L22', '1B24']
    d9 = ['1L10', '1B11', '1L24', '1B27']
    d10 = ['1L12', '1B13', '1L26', '1B30']
    d11 = ['1A16', '1H14', '1A24', '1G23', '1L88']
    d12 = ['1L14', '1B15', '1L28', '1B32']
    d13 = ['1G13', '1L78', '1C22', '1A32', '1A33']
    d14 = ['5G03', '1G03', '1L68', '5G09', '1G09', '1L74', '5G15', '1G15', '1L80', '5G21', '1G21', '1L86', '5U86']

    traindb.update_category_for_uids(d1, 'IEP 800/0 - Bi Mode -10 Car')
    traindb.update_category_for_uids(d2, 'IEP 800/3 - Bi Mode - 9 Car')
    traindb.update_category_for_uids(d3, 'IEP 802/0 - Bi Mode -10 Car')
    traindb.update_category_for_uids(d4, 'IEP 800/0 - Bi Mode -10 Car')
    traindb.update_category_for_uids(d5, 'IEP 802/1 - Bi Mode - 9 Car')
    traindb.update_category_for_uids(d6, 'IEP 800/3 - Bi Mode - 9 Car')
    traindb.update_category_for_uids(d7, 'IEP 800/0 - Bi Mode - 5 Car')
    traindb.update_category_for_uids(d8, 'IEP 800/0 - Bi Mode -10 Car')
    traindb.update_category_for_uids(d9, 'IEP 802/0 - Bi Mode -10 Car')
    traindb.update_category_for_uids(d10, 'IEP 800/3 - Bi Mode - 9 Car')
    traindb.update_category_for_uids(d11, 'IEP 800/0 - Bi Mode -10 Car')
    traindb.update_category_for_uids(d12, 'IEP 800/3 - Bi Mode - 9 Car')
    traindb.update_category_for_uids(d13, 'IEP 800/0 - Bi Mode -10 Car')
    traindb.update_category_for_uids(d14, 'IEP 800/0 - Bi Mode - 5 Car')

