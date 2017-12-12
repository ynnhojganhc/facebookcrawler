# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from selenium import webdriver
from lxml import etree
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from io import StringIO, BytesIO
from os.path import splitext
import os
import tempfile
import urllib
import re
import time
from abc import *

class Facebook():
    def __init__(self):
        self.users = {}
        return

    def add(self, user):
        self.users[user.uid] = user

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        fb = ""
        for n in self.users.values():
            fb += '%s\n' % (n)
        return u'%s' % fb

class FacebookUser(object):
    def __init__(self, name, uid):
        self.name = name
        self.uid = int(uid)
        self.friends = set()
        self.checked = False

    def uid(self): return self.uid

    def name(self): return self.name

    def add_friend(self, uid):
        self.friends.add(int(uid))

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        me = u'%d:%s\n' % (self.uid, self.name)
        friend = ""
        for f in self.friends:
            friend += ' -%d\n' % (f)
        return u'%s%s' % (me, friend)

class FacebookCrawler:
    def __init__(self, parser, facebook):
        self.facebook = facebook
        self.uid = re.compile(r'(?<=id=).\w*(?=&)')
        self.browser = webdriver.Firefox()
        self.facebookusername = os.environ['FB_USER']
        self.facebookpassword = os.environ['FB_PWD']
        self.fblogin = "https://m.facebook.com/login"
        self.profile_friend = "https://m.facebook.com/profile.php?v=friends&id={}"
        self.timeline = "https://m.facebook.com/profile.php?v=timeline&id={}"

        self.friend_xpath = '//*[@id="root"]//table[@role="presentation"]//a[@class="cc"]'
        self.profilename_xpath = '//*[@id="root"]//strong'
        self.feeds_xpath = '//div[@id="recent"]/div/div/div'
        if not isinstance(parser, IParser): raise Exception('Bad interface')
        if not IParser.version() == '1.0': raise Exception('Bad revision')
        self.parser = parser


        return

    def waitfor(self, cond, timeout=3):
        start_time = time.time()
        while time.time() < start_time + timeout:
            if cond():
                return True
            else:
                time.sleep(0.1)
        raise Exception('Timeout waiting for {}'.format(cond.__name__))

    def login(self):
        try:
            # fb mobile site login steps
            # locating elements by using xpath
            print(self.facebookusername)
            print(self.facebookpassword)
            def input_account():
                self.browser.find_element_by_xpath('//*[@id="login_form"]//input[@type="text"]').send_keys(self.facebookusername)
                self.browser.find_element_by_xpath('//*[@id="login_form"]//input[@type="password"]').send_keys(self.facebookpassword)
                self.browser.find_element_by_xpath('//*[@id="login_form"]//input[@name="login"]').click()

            def cofirm_login():
                self.browser.find_element_by_xpath('//form//input[@type="submit"]').send_keys(Keys.RETURN)

            self.getpage(self.fblogin, action=input_account)
            self.getpage(action=cofirm_login)


        except NoSuchElementException as e:
            print(e)

    def getpage(self, url=None, action=None):
        def complete():
            page_state = self.browser.execute_script(
                'return document.readyState;'
            )
            return page_state == 'complete'
        try:
            if url: self.browser.get(url)
            if action: action()
            self.waitfor(complete, timeout=5)
        except Exception as e:
            print e
        return

    def elements(self, xpath):
        return self.browser.find_elements_by_xpath(xpath)

    def element(self, xpath):
        return self.browser.find_element_by_xpath(xpath)

    def friends(self, uid, depth=1):
        if uid in self.facebook.users:
            u = self.facebook.users[uid]
            # check only when user is not checked
            if u.checked: return
            self.getpage(self.profile_friend.format(uid))
        else:
            self.getpage(self.profile_friend.format(uid))
            name = self.element(self.profilename_xpath).get_attribute('innerText')
            u = FacebookUser(name, uid)
            self.facebook.add(u)

        # get friend list only when depth > 1
        if depth < 1: return

        for e in self.elements(self.friend_xpath):
            try:
                name = e.get_attribute('innerText')
                uid = int(self.uid.search(e.get_attribute('href')).group(0))
                if uid not in self.facebook.users:
                    self.facebook.add(FacebookUser(name, uid))
                u.add_friend(uid)
            except Exception as e:
                print 'friend parse error:'+str(e)
                # [TODO] support faceboot non numeric uid
                return

        u.checked = True
        for f in list(u.friends):
            self.friends(f, depth-1)
        return

    def feeds(self, uid):
        self.getpage(self.timeline.format(uid))
        for feed in self.elements(self.friend_xpath):
            text = e.get_attribute('innerText')
            print text

class IParser:
    __metaclass__ = ABCMeta

    @classmethod
    def version(self): return "1.0"
    @abstractmethod
    def parse(self): raise NotImplementedError

# parse html by beautiful soup
class BSParser(IParser):
    def __init__(self):
        return
    def parseImage(self, soup):
        # for p in soup.find_all('img'):
        #    print p;
        for p in soup.find_all('div', attrs={'class': 'cp'}):
            # print p;
            for pp in p.find_all('img'):
                print(pp['src'])
                root, ext = splitext(pp['src'])
                urllib.urlretrieve(pp['src'], next(
                    tempfile._get_candidate_names()) + '.jpg')

    def parse(self, content):
        soup = BeautifulSoup(content, "html.parser")
        self.parseImage(soup)

# parse html by etree
class ETParser(IParser):
    def __init__(self):
        return
    def parseImp(self, html):
        profiles = html.xpath(u"//img[@class='l']")
        for p in profiles:
            print(p.attrib['src'])

    def parse(self, content):
        html = etree.HTML(content)
        self.parseImp(html)


def main():
    fb = Facebook()
    fc = FacebookCrawler(BSParser(), fb)
    fc.login()
    fc.friends(100015200389095, 6)
    for u in fb.users:
        fc.feeds(u)
    print u'%s' % fb


if __name__ == "__main__":
        main()
