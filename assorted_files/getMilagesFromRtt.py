import requests
from bs4 import BeautifulSoup

# pageurl = input(' Paste RTT link: ')
pageurl = 'https://www.realtimetrains.co.uk/train/W30253/2021-03-11/detailed'
# miles_from = input(' Miles start from: ')
miles_from = 'Reading [RDG]'

# The page we want to find the list of services for a station
page = requests.get(pageurl)

# Parse this into html
soup = BeautifulSoup(page.content, 'html.parser')

locations = soup.find('div', class_='locationlist')

# print(locations.find_all('div',class_='location'))

dict_of_locations = {}

for a in locations.find_all('div', class_='location'):
    if a.find('a', {'class': 'name'}) is not None and a.find('div', {'class': 'wtt'}) is not None:
        location = a.find('a', {'class': 'name'}).text

        if a.find('div', {'class': 'distance'}).find('span', {'class': 'miles'}) is not None:
            miles = a.find('div', {'class': 'distance'}).find('span', {'class': 'miles'}).text
        else:
            miles = None

        if a.find('div', {'class': 'distance'}).find('span', {'class': 'chains'}) is not None:
            chains = a.find('div', {'class': 'distance'}).find('span', {'class': 'chains'}).text
        else:
            chains = None

        if miles is not None and chains is not None:
            dict_of_locations[location] = int(miles) + (int(chains)/80)


new_0 = dict_of_locations[miles_from]
list_to_remove = []
for loc in dict_of_locations.keys():
    if dict_of_locations[loc] >= new_0:
        dict_of_locations[loc] = dict_of_locations[loc] - new_0
    else:
        list_to_remove.append(str(loc))

[dict_of_locations.pop(a) for a in list_to_remove]

with open('dist_from_rdg_to_bth.txt', 'w') as f_to_write:
    f_to_write.write(str(dict_of_locations))
