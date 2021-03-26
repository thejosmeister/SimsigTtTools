import requests
from bs4 import BeautifulSoup
import csv
import sys

# pageurl = sys.argv[1]
pageurl = 'https://www.realtimetrains.co.uk/train/V32895/2021-02-20/detailed'
# filename = 'test_locations'
# The page we want to find the list of services for a station
page = requests.get(pageurl)

# Parse this into html
soup = BeautifulSoup(page.content, 'html.parser')

locations = soup.find('div', class_='locationlist')

# print(locations.find_all('div',class_='location'))

dicts_of_locations = []

for a in locations.find_all('div', class_='location'):
    if a.find('a', {'class': 'name'}) is not None and a.find('div', {'class': 'wtt'}) is not None:
        location = {'location': a.find('a', {'class': 'name'}).text}

        # Arrival Times
        if a.find('div', {'class': 'wtt'}).find('div', {'class': 'arr'}) is not None:
            location['arr'] = a.find('div', {'class': 'wtt'}).find('div', {'class': 'arr'}).text.replace('½', '.5')

        # Departure Times
        if a.find('div', {'class': 'wtt'}).find('div', {'class': 'dep'}) is not None:
            location['dep'] = a.find('div', {'class': 'wtt'}).find('div', {'class': 'dep'}).text.replace('½', '.5')

        # Platform
        if a.find('div',{'class': 'platform'}) is not None:
            platform = a.find('div',{'class': 'platform'}).text
            if len(platform) > 0:
                location['plat'] = platform

        # Route
        if a.find('div', {'class': 'route'}) is not None:

            # Path
            if a.find('div', {'class': 'route'}).find('div', {'class': 'path act c'}) is not None:
                location['path'] = a.find('div', {'class': 'route'}).find('div', {'class': 'path act c'}).text
            if a.find('div', {'class': 'route'}).find('div', {'class': 'path exp c'}) is not None:
                location['path'] = a.find('div', {'class': 'route'}).find('div', {'class': 'path exp c'}).text

            # Line
            if a.find('div', {'class': 'route'}).find('div', {'class': 'line act c'}) is not None:
                location['line'] = a.find('div', {'class': 'route'}).find('div', {'class': 'line act c'}).text
            if a.find('div', {'class': 'route'}).find('div', {'class': 'line exp c'}) is not None:
                location['line'] = a.find('div', {'class': 'route'}).find('div', {'class': 'line exp c'}).text

        # Allowances
        addl = a.find('div', {'class': 'addl'})
        if addl is not None:
            allowance = addl.find('span', {'class': 'allowance'})
            if allowance is not None:
                if allowance.find('span', {'class': 'eng'}) is not None:

                    location['eng allow'] = allowance.find('span', {'class': 'eng'}).text.replace('½', '.5')
                if allowance.find('span', {'class': 'pth'}) is not None:
                    location['pth allow'] = allowance.find('span', {'class': 'pth'}).text.replace('½', '.5')
                if allowance.find('span', {'class': 'prf'}) is not None:
                    location['prf allow'] = allowance.find('span', {'class': 'prf'}).text.replace('½', '.5')


        dicts_of_locations.append(location)

import pprint

pp = pprint.PrettyPrinter(indent=4)

pp.pprint(dicts_of_locations)

header = soup.find('div', class_='header')
filename = header.text[:4] + '_locations'

with open(filename + '.csv', mode='w') as location_file:
    fieldnames = ['location', 'arr', 'dep']
    writer = csv.DictWriter(location_file, fieldnames=fieldnames)

    writer.writeheader()
    for row in dicts_of_locations:
        writer.writerow(row)

with open(filename + '.txt', 'w') as f_to_write:
    f_to_write.write(pp.pformat(dicts_of_locations))
