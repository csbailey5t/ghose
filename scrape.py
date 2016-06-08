from bs4 import BeautifulSoup
from functools import wraps
import pandas as pd
import re
import requests
from urllib.parse import urljoin

BASE_URL = 'http://www.indiastudycenter.com/Univ/Engineering-Colleges.asp'
SINGLE_URL = 'http://www.indiastudycenter.com/Univ/States/AP/Adilabad/AMR-Institute-Technology.asp'
ALT_URL = 'http://www.indiastudycenter.com/Univ/States/AP/Adilabad/jce.asp'


def with_default(default=None):
    """Wraps func. If the first value passed evaluates to True, call it. Otherwise, return default """

    def outer(func):
        """ actually wraps it """
        @wraps(func)
        def wrapper(first_arg, *args, **kwargs):
            """ This function wraps func """
            if first_arg:
                print('calling {} with {}'.format(func.__name__, first_arg))
                return func(first_arg, *args, **kwargs)
            else:
                print('not calling {} with {}'.format(func.__name__, first_arg))
                return default

        return wrapper

    return outer


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


@with_default((None, None, None))
def get_title_and_place(content):
    content = content.get_text()
    header = [field.strip() for field in content.split(',')]
    if len(header) == 3:
        title, district, state = header
    elif len(header) == 2:
        title, district = header
        state = None
    else:
        title = header[0]
        state = None
        district = None

    return title, district, state


@with_default((None, None))
def get_about_info(content):
    about_section = content.nextSibling
    about_contents = about_section.find_all('p')
    # establishment year
    establishment_line = about_contents[0].get_text()
    establishment_year = establishment_line.split(':')[1]
    establishment_year = establishment_year.strip()
    # institution type
    institution_line = about_contents[1].get_text()
    institution_type = institution_line.split(':')[1]
    institution_type = institution_type.strip()

    return establishment_year, institution_type


@with_default(None)
def get_pin(content):
    pin_line = content.find('p', text=re.compile('Pin'))
    if pin_line:
        pin_text = pin_line.get_text()
        pin_num = pin_text.split(':')[1]
        pin_num = pin_num.strip()
    else:
        pin_num = None
    return pin_num


@with_default(None)
def check_approval(content):
    if 'approved' and 'aicte' in content:
        approved = 'true'
    else:
        approved = 'false'
    return approved


@with_default((None, None, None, None))
def get_course_info(content):
    course_section = content[0].nextSibling
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
    if it_line:
        it_line = it_line.get_text()
        it_seats = re.findall('\d+\s\w+', it_line)
        num_it_seats = it_seats[0].split(' ')[0]
    else:
        num_it_seats = None
    # number of seats not it
    all_seats = re.findall('\d+\s\w+', course_text)
    if len(all_seats) == 0:
        total_seats = None
    else:
        nums = []
        for seat_num in all_seats:
            nums.append(seat_num.split(' ')[0])
        if num_it_seats:
            total_seats = 0 - int(num_it_seats)
        else:
            total_seats = 0
        for num in nums:
            total_seats += int(num)

    return has_masters, has_it, num_it_seats, total_seats


@with_default(None)
def get_head_dir(content):
    head = content.nextSibling.find('br').nextSibling
    return head


def get_college_info(url):
    # have to build in checks for every section since not every page has all
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    containing_div = soup.find('div', {'class': 'r'})

    # title, district, state
    title_and_place = containing_div.find('h1')
    print('title', title_and_place)
    title, district, state = get_title_and_place(title_and_place)

    about_section = containing_div.find('div', text=re.compile('About'))
    establishment_year, institution_type = get_about_info(about_section)

    # pin
    pin_section = containing_div.find('div', {'class': 'c'})
    pin_num = get_pin(pin_section)

    # Need to do recognition by AICTE or not
    # search for 'approved' and 'aicte' in lowered text of all areas
    all_text = containing_div.get_text().lower()
    approved = check_approval(all_text)

    course_section = containing_div.find_all(
        'div',
        text=re.compile('Courses')
        )
    has_masters, has_it, num_it_seats, total_seats = get_course_info(
        course_section
        )

    # head of dept
    who = containing_div.find('div', text=re.compile('Whos Who'))
    head = get_head_dir(who)

    row = [title, district, state, establishment_year,
           institution_type, pin_num, approved, has_masters,
           has_it, num_it_seats, total_seats, head]

    return row


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
               'pin', 'aicte approved', 'masters', 'it', 'it seats',
               'other seats', 'director']

    data = []
    # single_college = get_college_info(ALT_URL)
    single_college = get_college_info(SINGLE_URL)
    data.append(single_college)
    df = pd.DataFrame(data, columns=columns)
    # df.to_csv('colleges.csv')
    print(df)

if __name__ == '__main__':
    main()
