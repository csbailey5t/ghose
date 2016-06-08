from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin

BASE_URL = 'http://www.indiastudycenter.com/Univ/Engineering-Colleges.asp'


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


def main():
    college_groups_links = get_link_urls(BASE_URL)

    colleges = []
    for colleges_url in college_groups_links:
        colleges.append(get_link_urls(colleges_url))

    print(colleges)

if __name__ == '__main__':
    main()
