from dbClient import *

train_db = TrainTtDb('Swindon_A_&_B_IECC_-_SWINDID_130220')

# print(train_db.get_uid_for_headcode('1L10'))

train_db.update_origin_for_uids(train_db.get_uid_for_headcode('1L10'), 'SWANSEA', '0200')

print(train_db.get_tt_by_uid('Y94414'))
