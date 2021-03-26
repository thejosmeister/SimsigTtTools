import ast
from translateTimesAndLocations import convert_time_to_secs
import dbClient
import matplotlib.pyplot as plt
import re


def dist_rgd_to_bad():
    f = open('assorted_files/dist_from_rdg_to_bad.txt', "r")
    distances = ast.literal_eval(f.read())
    f.close()

    all_trains = dbClient.TrainTtDb('swindid_diversions_feb_21').get_all_in_db()

    pairs_of_times_and_values = []

    for train in all_trains:
        # if re.match("^(1(B|H|G)|(0|4|5|6).)\\d{2}$",train['headcode']):
            times = []
            mileages = []
            locations = train['locations']
            if 'entry_point' in train:
                if 'EDNMAIN' in train['entry_point'] or 'EDNRLF' in train['entry_point']:
                    times.append(convert_time_to_secs(train['entry_time']))
                    mileages.append(0)
                if 'EUPBAD' in train['entry_point']:
                    times.append(convert_time_to_secs(train['entry_time']))
                    mileages.append(64.0125)
            for location in locations:
                if location['location'] in distances:
                    if 'arr' in location:
                        times.append(convert_time_to_secs(location['arr']))
                        mileages.append(distances[location['location']])
                    if 'dep' in location:
                        times.append(convert_time_to_secs(location['dep']))
                        mileages.append(distances[location['location']])
            pairs_of_times_and_values.append([times, mileages, train['headcode']])


    plt.style.use('ggplot')
    # fig = plt.figure()
    # axes = fig.subplots(nrows=1, ncols=2)
    #
    # plot = axes[0]
    for i in range(len(pairs_of_times_and_values)):
        plt.plot(pairs_of_times_and_values[i][0], pairs_of_times_and_values[i][1], label=pairs_of_times_and_values[i][2])


    plt.legend(loc='upper right', fontsize='xx-small')
    # text = plot.text(-0.2,1.05, "Aribitrary text", transform=plot.transAxes)
    # fig.savefig('samplefigure', bbox_extra_artists=(lgd,text), bbox_inches='tight')
    plt.show()


def dist_rgd_to_bth():
    f = open('assorted_files/dist_from_rdg_to_bth.txt', "r")
    distances = ast.literal_eval(f.read())
    f.close()

    all_trains = dbClient.TrainTtDb('swindid_diversions_feb_21').get_all_in_db()

    pairs_of_times_and_values = []

    for train in all_trains:
        if re.match("^(1(A|L)|(4|5|6).)\\d{2}$",train['headcode']):
            times = []
            mileages = []
            locations = train['locations']
            if 'entry_point' in train:
                if 'EDNMAIN' in train['entry_point'] or 'EDNRLF' in train['entry_point']:
                    times.append(convert_time_to_secs(train['entry_time']))
                    mileages.append(0)
                if 'EUPMAIN' in train['entry_point']:
                    times.append(convert_time_to_secs(train['entry_time']))
                    mileages.append(68.625)
            for location in locations:
                if location['location'] in distances:
                    if 'arr' in location:
                        times.append(convert_time_to_secs(location['arr']))
                        mileages.append(distances[location['location']])
                    if 'dep' in location:
                        times.append(convert_time_to_secs(location['dep']))
                        mileages.append(distances[location['location']])
            pairs_of_times_and_values.append([times, mileages, train['headcode']])

    plt.style.use('ggplot')
    # fig = plt.figure()
    # axes = fig.subplots(nrows=1, ncols=2)

    # plot = axes[0]
    for i in range(len(pairs_of_times_and_values)):
        plt.plot(pairs_of_times_and_values[i][0], pairs_of_times_and_values[i][1],
                  label=pairs_of_times_and_values[i][2])

    plt.legend(loc='upper right', fontsize='xx-small')
    # text = plot.text(-0.2, 1.05, "Aribitrary text", transform=plot.transAxes)
    # fig.savefig('samplefigure', bbox_extra_artists=(lgd, text), bbox_inches='tight')
    plt.show()

dist_rgd_to_bad()