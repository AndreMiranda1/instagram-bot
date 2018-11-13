#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1st steps
"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from random import random, shuffle, choice
import time
from datetime import datetime

from ig_db_2 import execute_query


class AutoIG():
    # CLASS CONSTRUCTOR DOES THE LOGIN
    def __init__(self, username, password):
        self.username = username
        chrome_options = Options()
        chrome_options.add_argument("--disable-infobars")
        self.driver = webdriver.Chrome(options=chrome_options)

        self.driver.get("https://www.instagram.com/accounts/login/?source=auth_switcher&&lan=en")
        time.sleep(5 + 2 * random())
        username_field = self.driver.find_element_by_name("username")
        username_field.clear()
        username_field.send_keys(username)

        time.sleep(1 + 2 * random())
        password_field = self.driver.find_element_by_name("password")
        password_field.clear()
        password_field.send_keys(password)
        self.driver.find_elements_by_xpath("//button[contains(text(), 'Log in')]")[0].click()
        time.sleep(1 + random())

        query = 'INSERT INTO session (user_name, log_in) VALUES (%s, %s) RETURNING session_id'
        session_id = execute_query(query, (username, datetime.now()))[0][0]
        self.session_id = session_id
        query = '''UPDATE account SET last_session_id = %s, last_update = %s
                    WHERE user_name = %s;'''
        execute_query(query, (session_id, datetime.now().date(), username))

        print('Logged in with username: '.format(self.username))

    # Implements a random behaviour, to mimic a human user
    def action(self, type_of_action='random', max_actions=60):
        # Get hashtags for the user
        interests = self.get_interests()
        shuffle(interests)
        max_likes = 75
        max_follows = 35
        n_likes = 0
        n_follows = 0
        while True:
            for interest in interests:
                print('-----starting actions on {0} {1}-----'.format(interest[0], interest[1]))
                if interest[0] == 'hash':
                    interest_name = interest[1].lower()
                    self.driver.get("https://www.instagram.com/explore/tags/{0}/".format(interest_name))
                elif interest[0] == 'location':
                    interest_name = interest[1]
                    self.driver.get("https://www.instagram.com/explore/locations/{0}/?hl=eg".format(interest[1]))

                urls = self.fetch_urls(interest_name)
                urls = urls[:5]
                for url in urls:
                    if type_of_action == 'random':
                        action = choice(['like', 'like', 'like', 'like', 'follow', 'unfollow'])
                    elif type(type_of_action) == list:
                        action = choice(type_of_action)
                    elif type_of_action in ['like', 'follow', 'unfollow']:
                        action = type_of_action
                    else:
                        raise NameError('type_of_action not supported')

                    if action == 'like':
                        n_likes = n_likes + self.like_post(url)
                    elif action == 'follow':
                        n_follows = n_follows + self.follow_post(url)
                    elif action == 'unfollow':
                        n_follows = n_follows + self.unfollow_post()

                if n_likes >= max_likes:
                    print('----------------Finishing actions------------------')
                    return
                if n_follows >= max_follows:
                    print('----------------Finishing actions------------------')
                    return
                if n_likes + n_follows >= max_actions:
                    print('----------------Finishing actions------------------')
                    return

    def get_interests(self):
        interests = []

        # Get hashtags for the user
        query = 'SELECT interest_type, interest_name FROM interest WHERE user_name = %s AND active IS TRUE;'
        res = execute_query(query, (self.username, ))
        if res == []:
            print('user does not have interests, finishing')
            return interests
        interests = [[x[0], x[1]] for x in res]

        return interests

    def fetch_urls(self, interest, shuffle_urls=True):
        # Get scroll height
        SCROLL_PAUSE_TIME = 0.5
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # Wait to load page
            time.sleep(SCROLL_PAUSE_TIME)
            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        link_elements = self.driver.find_elements_by_xpath("//a[@href]")
        urls = [x.get_attribute("href") for x in link_elements]
        urls = [x for x in urls if x.endswith(interest)]
        if shuffle_urls:
            shuffle(urls)
        return urls

    def like_post(self, url):
        self.driver.get(url)
        try:
            self.driver.find_element_by_xpath("//span[contains(@aria-label, 'Like')]").click()
            print('like')
            time.sleep(1 + random())
            return 1
        except:
            print('already liked or page not found, continuing...')
            return 0

    def follow_post(self, url):
        self.driver.get(url)
        try:
            self.driver.find_elements_by_xpath("//button[contains(text(), 'Follow')]")[0].click()
            print('following')
            time.sleep(0.5)
            fol_elem = self.driver.find_elements_by_xpath("//div[@class='C4VMK']//a")[0]
            fol_name = fol_elem.get_attribute("title")

            query = '''INSERT INTO follow (user_name, followed_account, follow_date, follow_session_id)
                        VALUES (%s, %s, %s, %s);'''
            execute_query(query, (self.username, fol_name, datetime.now().date(), self.session_id))
            time.sleep(1 + random())
            return 1
        except IndexError:
            print('Already followng or page not found, continuing...')
            return 0

    def unfollow_post(self):
        query = '''SELECT followed_account FROM follow
        WHERE user_name = %s AND follow_date < %s AND unfollow_date IS NULL LIMIT 1;'''
        res = execute_query(query, (self.username, datetime.now().date()))

        if res != []:
            unfollow = res[0][0]
            self.driver.get("https://www.instagram.com/{0}/".format(unfollow))
            try:
                self.driver.find_elements_by_xpath("//button[contains(text(), 'Following')]")[0].click()
                print('unfollowing')
                time.sleep(1.5 + random())
                query = '''UPDATE follow SET unfollow_date = %s
                            WHERE user_name = %s AND followed_account = %s;'''
                execute_query(query, (datetime.now().date(), self.username, unfollow))
                return 1
            except IndexError:
                print('Already unfollow or page not found, continuing...')
        return 0

    def like_target(self, max_likes=20):
        print('start liking target account')
        query = '''SELECT target_name FROM target_account
                    WHERE user_name = %s AND active IS TRUE;'''
        res = execute_query(query, (self.username, ))

        if res == []:
            print('account does not have target accounts, skipping...')
            return

        targets = [x[0] for x in res]
        n_loops = 0
        n_likes = 0
        while True:
            target = choice(targets)
            self.driver.get("https://www.instagram.com/{0}/".format(target))
            urls = self.fetch_urls(target)
            url = urls[0]
            self.driver.get(url)
            try:
                self.driver.find_elements_by_class_name("zV_Nj")[0].click()
            except IndexError:
                pass
            time.sleep(1)
            elements = self.driver.find_elements_by_xpath("//div[contains(@class, 'd7ByH')]/a")
            accounts = [x.get_attribute("href") for x in elements]
            shuffle(accounts)
            accounts = accounts[: 5]
            for account in accounts:
                self.driver.get(account)
                urls = self.fetch_urls(account.split('/')[-2])
                urls = urls[: 3]
                for url in urls:
                    n_likes = n_likes + self.like_post(url)
                    if n_likes >= max_likes or n_loops >= 10:
                        print('finished liking targets')
                        return
            n_loops += 1

    def log_out(self):
        self.driver.get("https://www.instagram.com/{0}/".format(self.username))

        # Save tracking
        x_path = "//a[@href='/{0}/followers/']//span".format(self.username)
        followers = int(self.driver.find_element_by_xpath(x_path).text)
        query = '''INSERT INTO tracking (user_name, followers, session_tracking_id, tracking_date)
                    VALUES (%s, %s, %s, %s);'''
        execute_query(query, (self.username, followers, self.session_id, datetime.now()))

        self.driver.find_element_by_xpath("//span[contains(@aria-label, 'Options')]").click()
        time.sleep(random())

        self.driver.find_elements_by_xpath("//button[contains(text(), 'Log Out')]")[0].click()
        time.sleep(random())
        self.driver.delete_all_cookies()
        self.driver.close()

        query = 'UPDATE session SET log_out = %s WHERE session_id = %s'
        execute_query(query, (datetime.now(), self.session_id))
        print('Logged out and Closed Session from username: '.format(self.username))
        return 'ok'
