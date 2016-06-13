from bs4 import BeautifulSoup
from functools import wraps
import pandas as pd
import re
import requests
from urllib.parse import urljoin

# Set the URL to start the scrape from
BASE_URL = 'http://www.indiastudycenter.com/Univ/Engineering-Colleges.asp'
# Set two URLS to test the script. SINGLE_URL is a page with good markup
# ALT_URL is a page with the lesson common but still used table markup
SINGLE_URL = 'http://www.indiastudycenter.com/Univ/States/AP/Adilabad/AMR-Institute-Technology.asp'
ALT_URL = 'http://www.indiastudycenter.com/Univ/States/AP/Adilabad/jsncet.asp'


def with_default(default=None):
    """Wraps func. If the first value passed evaluates to True, call it.
     Otherwise, return default """

    def outer(func):
        """ actually wraps it """
        @wraps(func)
        def wrapper(first_arg, *args, **kwargs):
            """ This function wraps func """
            if first_arg:
                # print('calling {} with {}'.format(func.__name__, first_arg))
                return func(first_arg, *args, **kwargs)
            else:
                # print('not calling {} with {}'.format(func.__name__, first_arg))
                return default

        return wrapper

    return outer


def get_link_urls(url):
    """ Creates a list of urls for colleges scraped from the given url """
    # Get the raw html
    page = requests.get(url)
    # Create a BS4 object with the html
    soup = BeautifulSoup(page.text, 'html.parser')
    # Get the div that contains the content on the right side of the page
    containing_div = soup.find('div', {'class': 'r'})
    # Within that div, get the list of college groups
    college_groups = containing_div.find('div', {'class': 'c'})
    # Create an empty list to store the urls
    college_groups_links = []
    # Iterate over all links in the college groups, build the url
    # and then append it to the list of urls
    for a in college_groups.find_all('a', href=True):
        group_link = urljoin(page.url, a['href'])
        college_groups_links.append(group_link)

    return college_groups_links


def flatten(content):
    """ Given a list of lists, return a flat list """
    flat_list = [item for sublist in content for item in sublist]
    return flat_list


# Wrap each content grabbing function so that if the content isn't there
# it returns None for that piece of content
@with_default((None, None, None))
def get_title_and_place(content):
    """ Grabs college name and location """
    # Get the text of the title and location header
    content = content.get_text()
    # Split it on commas and strip out whitespace
    header = [field.strip() for field in content.split(',')]
    # Depending on the number of elements, return content
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
    """ Grabs content pieces from the about area """
    # Find the about section
    about_section = content.nextSibling
    # If the establishment year is there, get it. Otherwise, set it to None.
    if about_section.find('p', text=re.compile('Establishment')):
        establishment_line = about_section.find(
            'p', text=re.compile('Establishment')
            ).get_text()
        establishment_year = establishment_line.split(':')[1]
        establishment_year = establishment_year.strip()
    else:
        establishment_year = None
    # If the Institution type is listed, get it. Otherwise, set to None.
    if about_section.find('p', text=re.compile('Institution Type:')):
        institution_line = about_section.find(
            'p', text=re.compile('Institution')
            ).get_text()
        institution_type = institution_line.split(':')[1]
        institution_type = institution_type.strip()
    else:
        institution_type = None
    return establishment_year, institution_type


@with_default(None)
def get_pin(content):
    """ Grabs the college's PIN """
    # Find the pin line
    pin_line = content.find('p', text=re.compile('Pin'))
    # If there is a pin line, get the PIN. Otherwise, set to None.
    if pin_line:
        pin_text = pin_line.get_text()
        pin_num = pin_text.split(':')[1]
        pin_num = pin_num.strip()
    else:
        pin_num = None
    return pin_num


@with_default(None)
def check_approval(content):
    """ Checks for approval by AICTE """
    # Look for 'approved' and 'aicte'. If there, set approval to true.
    # If not, false.
    if 'approved' and 'aicte' in content:
        approved = 'true'
    else:
        approved = 'false'
    return approved


@with_default((None, None, None, None))
def get_course_info(content):
    """ Grab information from the course content block """
    # Find the course section
    course_section = content[0].nextSibling
    # Get the text and lowercase it
    course_text = course_section.get_text().lower()
    # Check if has masters degree or not
    if 'master' in course_text:
        has_masters = 'true'
    else:
        has_masters = 'false'
    # Check if has IT classes or not
    # TODO: if finding 'it' make sure it picks that up only when it constitutes the entire word
    # TODO: consider looking specifically for 'IT' in text blog that is not lower cased.
    if 'information technology' or 'it' in course_text:
        has_it = 'true'
    else:
        has_it = 'false'
    # Calculate the number of IT seats
    # Find the IT line
    it_line = course_section.find('p', text=re.compile('Information'))
    # If the line exists, find all '## seats' phrases. Just get the number.
    # TODO: check for situation based on 'IT' to make sure count is accurate
    if it_line:
        it_line = it_line.get_text()
        it_seats = re.findall('\d+\s\w+', it_line)
        if len(it_seats) > 0:
            num_it_seats = it_seats[0].split(' ')[0]
        else:
            num_it_seats = None
    else:
        num_it_seats = None
    # Calculate the number of non-IT seats
    # Find all "## seats" phrases
    all_seats = re.findall(r'\d+ \w+', course_text)
    # If no such phrases, set seats to None
    if len(all_seats) == 0:
        total_seats = None
    else:
        nums = []
        for seat_num in all_seats:
            nums.append(seat_num.split(' ')[0])
        # If there are IT seats, subtract them from the total seats
        if num_it_seats:
            total_seats = 0 - int(num_it_seats)
        else:
            total_seats = 0
        # Add seat numbers to get total seats
        for num in nums:
            total_seats += int(num)

    return has_masters, has_it, num_it_seats, total_seats


@with_default(None)
def get_head_dir(content):
    """ Grabs the head of the college """
    head = content.nextSibling.find('br').nextSibling
    return head


def get_college_info(url):
    """ Scrapes the information for each college from the url given
    where the url is for a single college page """
    # Get the raw page html
    page = requests.get(url)
    # Make a BeautifulSoup object from the html
    soup = BeautifulSoup(page.text, 'html.parser')
    # Handle one of the lesson comment but existing problem pages
    # where there is a page for a college,
    # but no content other than a selection list
    # Set the title and url to the URL and everything else to none
    if soup.find('strong', text=re.compile('Choose a University')):
        title = url

        district, state, establishment_year = (None, None, None)
        institution_type, pin_num, has_masters = (None, None, None)
        num_it_seats, total_seats, head = (None, None, None)
        has_it, approved = (None, None)

        row = [title, district, state, establishment_year,
               institution_type, pin_num, approved, has_masters,
               has_it, num_it_seats, total_seats, head, url]

        return row
    # Handle the pages with the most common, good markup
    # Determines if the page is such by presence of various content areas
    elif soup.find('div', text=re.compile('Courses')) or soup.find(
        'div', text=re.compile('About')
    ) or soup.find('div', text=re.compile('Engineering Updates')):

        containing_div = soup.find('div', {'class': 'r'})

        # Each section below grabs the data from different content sections
        # using the functions for each section above
        # Title and location section
        if containing_div.find('h1'):
            title_and_place = containing_div.find('h1')
        elif containing_div.find('div', {'class': 'head'}):
            title_and_place = containing_div.find('div', {'class': 'head'})
        else:
            title_and_place = None
        if title_and_place is None:
            title = url
            district, state = (None, None)
        else:
            title, district, state = get_title_and_place(title_and_place)

        # About section
        about_section = containing_div.find('div', text=re.compile('About'))
        establishment_year, institution_type = get_about_info(about_section)

        # PIN
        pin_section = containing_div.find('div', {'class': 'c'})
        pin_num = get_pin(pin_section)

        # AICTE approval
        all_text = containing_div.get_text().lower()
        approved = check_approval(all_text)

        # Course section
        course_section = containing_div.find_all(
            'div',
            text=re.compile('Courses')
            )
        has_masters, has_it, num_it_seats, total_seats = get_course_info(
            course_section
            )

        # Head/Director section
        who = containing_div.find('div', text=re.compile('Whos Who'))
        head = get_head_dir(who)

        # Build the data row
        row = [title, district, state, establishment_year,
               institution_type, pin_num, approved, has_masters,
               has_it, num_it_seats, total_seats, head, url]

        return row
    # Handle the pages where the markup for the college is a table
    else:
        # Add check for 'Established in: YYYY'
        # If it has it, pull the year and attach
        # Get the title of the college
        title_block = soup.find('td', {'class': 'grn'})
        title = title_block.find('strong').get_text()
        title = title.strip()
        # Check for AICTE approval
        about_content = soup.find('td', {'class': 'crm'}).get_text().lower()
        if 'approved' and 'aicte' in about_content:
            approved = 'true'
        else:
            approved = 'false'
        # Check for presence of Information Technology
        if len(soup.find_all('td', {'class': 'crm'})) > 1:
            course_list = soup.find_all('td', {'class': 'crm'})[1]
            course_text = course_list.get_text().lower()
            if 'it' in course_text:
                has_it = 'true'
            else:
                has_it = 'false'
        else:
            has_it = 'false'

        # Set defaults for information not on these pages
        district, state, establishment_year = (None, None, None)
        institution_type, pin_num, has_masters = (None, None, None)
        num_it_seats, total_seats, head = (None, None, None)
        # Build the data row
        row = [title, district, state, establishment_year,
               institution_type, pin_num, approved, has_masters,
               has_it, num_it_seats, total_seats, head, url]

        return row


def main():
    # Get the first list of urls from the start page
    college_groups_links = get_link_urls(BASE_URL)
    # Create an empty list to collect groups of urls
    area_colleges_urls = []
    # Get the next set of urls for the first level of subpages
    for colleges_url in college_groups_links:
        area_colleges_urls.append(get_link_urls(colleges_url))
    # Flatten the list of lists to make it easier to iterate over
    flat_area_colleges_urls = flatten(area_colleges_urls)
    # Create a empty list to collect college page urls
    college_urls = []
    # Iterate over subpage urls to build college url list
    for college_url in flat_area_colleges_urls:
        college_urls.append(get_link_urls(college_url))
    # Flatten the list of lists for ease of use
    flat_college_urls = flatten(college_urls)
    # Define urls that return page content that doesn't fit any schema
    # Many of these are bad urls that redirect to a generic search page
    bad_urls = [
        'http://www.indiastudycenter.com/Univ/Engineering-Colleges.asp',
        'http://www.indiastudycenter.com/Univ/Admission7.htm',
        'http://www.indiastudycenter.com/Univ/States/AP/hydbad/hydengc.asp',
        'http://www.indiastudycenter.com/Univ/States/AP/Rangardy/Rangaengg.asp',
        'http://twitter.com/share',
        'http://www.indiastudycenter.com/Univ/States/Karnataka/Bangalore(Urban)/amrita_institute_of_technology_&_sc.asp',
        'http://www.indiastudycenter.com/Univ/States/Karnataka/Bangalore/bit.asp',
        'http://www.indiastudycenter.com/Univ/States/Karnataka/Bangalore(Urban)/b-t-l-institute_of_technology_&_manageme.asp',
        'http://www.indiastudycenter.com/Univ/States/Karnataka/Bangalore(Urban)/nagarjuna_college_of_engg_&_tech.asp',
        'http://www.indiastudycenter.com/Univ/States/Karnataka/Bangalore(Urban)/reva_institute_for_science_&_technology.asp',
        'http://www.indiastudycenter.com/Univ/States/Karnataka/Bangalore(Urban)/University_vishweshwaraiah_college_of_en.asp',
        'http://www.indiastudycenter.com/univ/states/kerala/kozhikode/AWH-Engineering-College.asp',
        'http://www.indiastudycenter.com/Univ/States/Maharastra/Dr-Babasaheb-Ambedkar-Marathwada-University/Faculties-Departments/Chemistry.asp',
        "http://www.indiastudycenter.com/Univ/States/Maharastra/Pune/Marathwada-Mitra-Mandal'S-College-of-Engineering-Karvenagar.asp",
        'http://www.indiastudycenter.com/Univ/States/Maharastra/Raigad/kgce.asp',
        'http://www.indiastudycenter.com/univ/examinfo/uajet/default.asp'
    ]

    # urls to be done manually:
    # http://www.indiastudycenter.com/Univ/States/Karnataka/Bangalore/bit.asp
    # http://www.indiastudycenter.com/Univ/States/Karnataka/Bangalore(Urban)/University_vishweshwaraiah_college_of_en.asp
    # http://www.indiastudycenter.com/univ/states/kerala/kozhikode/AWH-Engineering-College.asp
    # http://www.indiastudycenter.com/Univ/States/Maharastra/Dr-Babasaheb-Ambedkar-Marathwada-University/Faculties-Departments/Chemistry.asp
    # http://www.indiastudycenter.com/Univ/States/Maharastra/Raigad/kgce.asp

    # Clean the list of college urls to remove bad urls
    clean_college_urls = [x for x in flat_college_urls if x not in bad_urls]
    # Define column names for the dataframe
    columns = ['title', 'district', 'state', 'year', 'type',
               'pin', 'aicte approved', 'masters', 'it', 'it seats',
               'other seats', 'director', 'url']
    # Create an empty list to contain the data
    data = []
    # Iterate over the college pages, scraping the college info
    for college_url in clean_college_urls:
        # Print the college url so we see where we're at when the script runs
        print(college_url)
        # Get the info and append the data row to the data set
        college_info = get_college_info(college_url)
        data.append(college_info)
    # The following lines were used to scrape single pages to test
    # the scraping function
    # single_college = get_college_info(ALT_URL)
    # single_college = get_college_info(SINGLE_URL)

    # Create a pandas DataFrame from the data and column names
    df = pd.DataFrame(data, columns=columns)
    # Make a CSV file from the dataframe
    df.to_csv('colleges.csv')
    # Tell you the script is finished.
    print('all done.')

if __name__ == '__main__':
    main()
