from bs4 import BeautifulSoup
import pandas as pd
import re
import requests
from urllib.parse import urljoin

BASE_URL = 'http://www.indiastudycenter.com/Univ/Engineering-Colleges.asp'
SINGLE_URL = 'http://www.indiastudycenter.com/Univ/States/AP/Adilabad/AMR-Institute-Technology.asp'


def get_link_urls(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    containing_div = soup.find('div', {'class': 'r'})
    college_groups = containing_div.find('div', {'class': 'c'})
    college_groups_links = []
    for a in college_groups.find_all('a', href=True):
        group_link = urljoin(page.url, a['href'])
        college_groups_links.append(group_link)

    return college_groups_links


def flatten(content):
    flat_list = [item for sublist in content for item in sublist]
    return flat_list


def get_college_info(url):
    # have to build in checks for every section since not every page has all
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    containing_div = soup.find('div', {'class': 'r'})

    # title, distrcit, state
    title_and_place = containing_div.find('h1').get_text()
    title, district, state = title_and_place.split(',')
    district = district.strip()
    state = state.strip()

    about_section = containing_div.find_all('div', {'class': 'c'})[1]
    about_contents = about_section.find_all('p')
    # establishment year
    establishment_line = about_contents[0].get_text()
    establishment_year = establishment_line.split(':')[1]
    establishment_year = establishment_year.strip()
    # institution type
    institution_line = about_contents[1].get_text()
    institution_type = institution_line.split(':')[1]
    institution_type = institution_type.strip()

    # pin
    pin_section = containing_div.find('div', {'class': 'c'})
    pin_line = pin_section.find_all('p')[1].get_text()
    pin_num = pin_line.split(':')[1]
    pin_num = pin_num.strip()

    # Need to do recognition by AICTE or not
    # search for 'approved' and 'aicte' in lowered text of all areas
    all_text = containing_div.get_text()

    course_section = containing_div.find_all('div', {'class': 'c'})[2]
    course_text = course_section.get_text().lower()
    # has masters degree or not
    if 'master' in course_text:
        has_masters = 'true'
    else:
        has_masters = 'false'
    # has it classes or not
    if 'information technology' or 'it' in course_text:
        has_it = 'true'
    else:
        has_it = 'false'
    # number of it seats
    it_line = course_section.find('p', text=re.compile('Information'))
    it_line = it_line.get_text()
    it_seats = re.findall('\d+\s\w+', it_line)
    num_it_seats = it_seats[0].split(' ')[0]
    # number of seats not it
    all_seats = re.findall('\d+\s\w+', course_text)
    nums = []
    for seat_num in all_seats:
        nums.append(seat_num.split(' ')[0])
    total_seats = 0 - int(num_it_seats)
    for num in nums:
        total_seats += int(num)

    # head of dept
    who = containing_div.find('div', text=re.compile('Whos Who'))
    head = who.nextSibling.find('br').nextSibling

    row = [title, district, state, establishment_year,
           institution_type, pin_num, has_masters, has_it, num_it_seats,
           total_seats, head]

    return all_text


def main():
    # college_groups_links = get_link_urls(BASE_URL)
    #
    # area_colleges_urls = []
    # for colleges_url in college_groups_links:
    #     area_colleges_urls.append(get_link_urls(colleges_url))
    #
    # # flatten list
    # flat_area_colleges_urls = flatten(area_colleges_urls)
    #
    # college_urls = []
    # for college_url in flat_area_colleges_urls:
    #     college_urls.append(get_link_urls(college_url))
    #
    # flat_college_urls = flatten(college_urls)

    columns = ['title', 'district', 'state', 'year', 'type',
               'pin', 'masters', 'it', 'it seats', 'other seats' 'director']

    # data = []
    single_college = get_college_info(SINGLE_URL)
    # data.append(single_college)
    # df = pd.DataFrame(data, columns=columns)
    print(single_college)

if __name__ == '__main__':
    main()
