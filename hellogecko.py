from selenium import webdriver
from lxml import etree


browser = webdriver.Firefox()

prochar = '[(=\-\+\:/&<>;|\'"\?%#$@\,\._)]'
like = re.compile(r'(.*)(?= L)')
comment = re.compile(r'(.*)(?= C)')
share = re.compile(r'(?<=Comments )(.*)(?= S)')

# Get content by soup
contenct = browser.get('https://m.facebook.com/profile.php?id=100022449967331')
soup = BeautifulSoup(content, "html.parser")

pause()
# Get content by etree
selector = etree.HTML(contenct)
profiles = selector.xpath('//h4/a/text()')
for p in profiles:
    print link
