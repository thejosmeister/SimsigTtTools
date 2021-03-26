import requests
from bs4 import BeautifulSoup
import time

pages = [ 'https://www.realtimetrains.co.uk/search/detailed/WKF/2021-01-12/1400-1800?stp=WVS&show=all&order=wtt&toc=GR' ]

for main_rtt_page in pages:

    # The page we want to find the list of services for a station
    page = requests.get(main_rtt_page)

    #Parse this into html
    soup = BeautifulSoup(page.content, 'html.parser')

    # This will find all the trains listed on the page
    trains = soup.find_all('a', class_='service')

    # We want to pull out all the trains that have their numbers listed
    # The href gives this away as it will have an 'allox' 
    def pull_out_trains_with_numbers(trains: list) -> list:
        out = []
        for train in trains:
            if 'allox' in train['href']:
                out.append(train)
        return out

    trains_with_nums = pull_out_trains_with_numbers(trains)
        
    # Now collect the hrefs of the trains we want to look at.
    hrefs = []
    for stop in trains_with_nums:
        hrefs.append(stop['href'])

    # This will get the respective pages for each train and check that the allocation is correct for the particular
    # portion of the journey. The numbers will then be appended to a list.
    # We can make the list into a set to see which units were on the diagrams for the day.

    base_url = 'https://www.realtimetrains.co.uk'
    numbers = []
    dict_of_services = {}
    for href in hrefs:
        
        servicePage = requests.get(base_url + href)
        parsed_html = BeautifulSoup(servicePage.content, 'html.parser')
        nums_to_add = []
        # The case where there are multiple changes in diag
        initial_div = parsed_html.find('div', allocation_id=href[-1])
        if initial_div != None:
            nums_to_add = initial_div.find_all('span', class_='identity')
        
        if len(nums_to_add) == 0:
            # Some (freight) just have the alloc in a different place so add here.
            nums_to_add.append(parsed_html.find('div', class_='allocation').find('span'))
        
        # Find headcode
        headcode = parsed_html.find(id='servicetitle').find('div', class_='header').text[:4]
        
        services_with_headcode = ''
        
        for num in nums_to_add:
            if num != None:
                numbers.append(num.text)
                services_with_headcode += num.text + ' '
                print(num.text + ' : ' + headcode)
        
        dict_of_services[headcode] = services_with_headcode
        
        time.sleep(1)

    filename = main_rtt_page[main_rtt_page.rfind('detailed/')+9:main_rtt_page.rfind('?')].replace('/','_')
    with open(filename + '.txt', 'w') as f:
        print('List of services:', file=f)
        print(' ', file=f)
        for key in dict_of_services:
            print(key, '->', dict_of_services[key], file=f)
        print(' ', file=f)
        print('All numbers present:', file=f)
        print(' ', file=f)
        for num in set(numbers):
            print(num, file=f)
