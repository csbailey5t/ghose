from bs4 import BeautifulSoup
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
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    containing_div = soup.find('div', {'class': 'r'})

    title_and_place = containing_div.find('h1').get_text()
    title, district, state = title_and_place.split(',')
    district = district.strip()
    state = state.strip()

    about_section = containing_div.find_all('div', {'class': 'c'})[1]
    establishment_line = about_section.find('p').get_text()
    establishment_year = establishment_line.split(':')[1]
    establishment_year = establishment_year.strip()

    return establishment_year


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

    single_college = get_college_info(SINGLE_URL)
    print(single_college)

if __name__ == '__main__':
    main()
