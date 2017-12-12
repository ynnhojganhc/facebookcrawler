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
import codecs
import locale
import sys

# Wrap sys.stdout into a StreamWriter to allow writing unicode.
sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)

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
    def __init__(self, facebook):
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

    def back(self):
        self.browser.back()

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
            time.sleep(1)
        except Exception as e:
            print e
        return

    def elements(self, xpath, e=None):
        if e is not None:
            return e.find_elements_by_xpath(xpath)
        else:
            return self.browser.find_elements_by_xpath(xpath)

    def element(self, xpath, e=None):
        if e is not None:
            return e.find_element_by_xpath(xpath)
        else:
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

    def reply(self, link, keyword):
        self.getpage(link)
        content = self.element('//div[@id="root"]')
        text = content.get_attribute('innerText')
        if keyword.lower() in text.lower():
            print link
            print text

    def photo(self, link, keyword):
        self.getpage(link)
        content = self.element('//div[@id="MPhotoContent"]')
        text = self.element('./div[1]/div[1]', content).get_attribute('innerText')
        if keyword.lower() in text.lower():
            print link
            print text
        for m in self.elements('//div[contains(@id, "comment_replies_mor")]'):
            more = self.element('.//a[contains(@href, "replies")]', m)
            self.reply(more.get_attribute('href'), keyword)

    def feeds(self, uid, keyword):
        self.getpage(self.timeline.format(uid))
        while True:
            # try to get next page
            next = None
            try:
                more = self.element('.//a[contains(@href, "profile.php?sectionLoadingID")]')
                next = more.get_attribute('href')
            except:
                return

            msglinks = set()
            for feed in self.elements(self.feeds_xpath):
                text = ''
                for p in self.elements('.//p',feed):
                    text += p.get_attribute('innerText')
                if keyword.lower() in text.lower():
                    # check messages
                    link = self.element('.//a[contains(@href, "footer_action_list")]', feed)
                    msglinks.add((link.get_attribute('href'), text))
            for p,t in list(msglinks):
                self.getpage(p)
                print u'%s' % t
                ee = self.elements('//div[substring(@id, 0) > 0]')
                photos = []
                for e in ee:
                    try:
                        print ' user:%s' % self.element('.//h3', e).get_attribute('innerText')
                        msg = e.get_attribute('innerText')
                        msg = msg[msg.find('\n')+1:msg.rfind('\n')]
                        print'  msg:%s' % msg
                    except:
                        continue
                for photo in self.elements('.//a[contains(@href, "photo.php")]'):
                    photos.append(photo.get_attribute('href'))
                for photo in photos:
                    self.photo(photo, keyword)

            if next is None: break
            self.getpage(next)

def main():
    fb = Facebook()
    fc = FacebookCrawler(fb)
    fc.login()
    fc.friends(100015200389095, 6)
    #fc.reply("https://m.facebook.com/comment/replies/?ctoken=115828865861858_117869358991142&count=3&curr&pc=1&ft_ent_identifier=115828865861858&gfid=AQAfyhofKnFWbyC5&refid=13&__tn__=R", 'BOSS')
    for u in fb.users:
        fc.feeds(u, 'Boss')
    print u'%s' % fb


if __name__ == "__main__":
        main()
