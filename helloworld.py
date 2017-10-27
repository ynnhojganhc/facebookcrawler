from bs4 import BeautifulSoup   
from selenium import webdriver
from lxml import etree
from io import StringIO, BytesIO
from os.path import splitext
import tempfile
import urllib
import re

browser = webdriver.Firefox()

prochar = '[(=\-\+\:/&<>;|\'"\?%#$@\,\._)]'
like = re.compile(r'(.*)(?= L)')
comment = re.compile(r'(.*)(?= C)')
share = re.compile(r'(?<=Comments )(.*)(?= S)')

u = "https://m.facebook.com/profile.php?id=100022449967331"
#//*[@id="profile_photos_unit"]/div/div/div/div[1]/a/div/div[3]/div/i
#//*[@id="profile_photos_unit"]/div/div/div/div[1]/a/div/div[1]/div/i

## retrieve page source after browser rendering
def get_html(url):
    browser.get(url)
    return browser.page_source

# Get content by soup for element - "div", {"id": "articlebody"}
def parse_soup(c):
    soup = BeautifulSoup(c, "html.parser")
    #for p in soup.find_all('img'):
    #    print p;
    for p in soup.find_all('div', attrs={'class':'cp'}):
        #print p;
        for pp in p.find_all('img'):
            print pp['src']
            root, ext = splitext(pp['src'])
            urllib.urlretrieve(pp['src'], next(tempfile._get_candidate_names()) + '.jpg')

# Get content by etree
def parse_etree(c):
    html = etree.HTML(c)
    profiles =html.xpath(u"//img[@class='l']")
    for p in profiles:
        print p.attrib['src']

def main():
    c = get_html(u)
    parse_soup(c)
    parse_etree(c)

if __name__ == "__main__":
    main()



