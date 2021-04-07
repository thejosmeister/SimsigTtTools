import xml.etree.ElementTree as ET
import zipfile
import os

def pull_tiploc_out_of_xml(files_to_pull_tiploc_out: list, out_filename):
    """
    Will fetch any location codes within Simsig TTs for the same sim and output a list to a text file.
    Separates the entry locations from others.
    I used it to create a dictionary of locations in a sim where there is not one provided in the documentation.

    :param files_to_pull_tiploc_out: The Simsig TT.
    :param out_filename: Name of ouput file.
    """
    entry_points = []
    locations = []
    for file_to_pull_tiploc_out in files_to_pull_tiploc_out:
        with zipfile.ZipFile(file_to_pull_tiploc_out, 'r') as zip_ref:
            zip_ref.extractall('temp_parsing_dir')

        tree = ET.parse('temp_parsing_dir/SavedTimetable.xml')

        os.remove('temp_parsing_dir/SavedTimetable.xml')
        os.remove('temp_parsing_dir/TimetableHeader.xml')
        os.rmdir('temp_parsing_dir')

        root = tree.getroot()

        timetables = root.find('Timetables')
        for tt in timetables.findall('Timetable'):
            if tt.find('EntryPoint') is not None:
                entry_points.append(tt.find('EntryPoint').text)

            trips = tt.find('Trips')
            for l in trips.findall('Trip'):
                locations.append(l.find('Location').text)

    set_of_entry_points = sorted(list(set(entry_points)))
    set_of_locations = sorted(list(set(locations)))

    with open(out_filename, mode='w') as emails_file:
        print('entry_points: ', file=emails_file)
        for e in set_of_entry_points:
            print(f'  {e}:', file=emails_file)
            print('    readable_names:', file=emails_file)
            print('    assoc_sim_location:', file=emails_file)
        print(' ', file=emails_file)
        print('locations: ', file=emails_file)
        for e in set_of_locations:
            print(f'  {e}:', file=emails_file)


if __name__ == '__main__':
    pull_tiploc_out_of_xml(['C:/Users/josiah.filleul/PycharmProjects/SimsigTtTools/assorted_files/Newport SO 21 11 2015 0000 Start.WTT'],
                           'test.yaml')
