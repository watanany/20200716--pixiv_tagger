#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import re
import time
import pickle
from IPython import embed
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

PIXIV_ID = os.getenv('PIXIV_ID')
PASSWORD = os.getenv('PIXIV_PASSWORD')
NUM_ILLUSTS_PER_PAGE = 4 * 5

class Tagger:
    def __init__(self, pixiv_id, password):
        self.pixiv_id = pixiv_id
        self.password = password
        self.driver = webdriver.Chrome()
        self.cache_file = '/Users/watanabe_shingo/projects/pixiv_tagger/cache/edit_links.pkl'

    def __enter__(self):
        self.driver = webdriver.Chrome()
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.driver.close()

    def bookmark_index(self, page):
        return 'http://www.pixiv.net/bookmark.php?rest=show&p={}'.format(page)

    def login(self):
        self.driver.get('https://accounts.pixiv.net/login')
        login_form = self.driver.find_element_by_css_selector('div#container-login form')
        login_form.find_element_by_css_selector('input[type=text]').send_keys(self.pixiv_id)
        login_form.find_element_by_css_selector('input[type=password]').send_keys(self.password)
        login_form.submit()
        return self

    def get_num_bookmarks(self):
        self.driver.get(self.bookmark_index(1))
        m = re.search(r'\((\d+)\)',
                      self.driver.find_element_by_css_selector('a.bookmark-tag-all').get_attribute('innerHTML'))
        return int(m.group(1))

    def get_num_bookmark_index(self):
        num_bookmarks = self.get_num_bookmarks()
        num_bookmark_index = 0
        num_bookmark_index += num_bookmarks // NUM_ILLUSTS_PER_PAGE
        num_bookmark_index += num_bookmarks % NUM_ILLUSTS_PER_PAGE
        return num_bookmark_index

    def get_edit_links(self):
        edit_links = self.get_edit_links_cache()

        for page in range(1, self.get_num_bookmark_index()):
            self.driver.get(self.bookmark_index(page))
            s = { a.get_attribute('href') for a in self.driver.find_elements_by_css_selector('a.edit-work') }
            if len(edit_links & s) == 0:
                edit_links |= s
            else:
                break

        with open(self.cache_file, 'wb') as w:
            pickle.dump(edit_links, w)

        return edit_links

    def get_edit_links_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'rb') as r:
                return pickle.load(r)
        else:
            return set()

    def autotag(self):
        edit_links = sorted(self.get_edit_links())
        for i, edit_link in enumerate(edit_links):
            try:
                self.driver.get(edit_link)

                recommend_tags = { span.get_attribute('data-tag')
                                   for span in self.driver.find_elements_by_css_selector('section.work-tags-container span[data-tag]') }
                cloud_tags = { span.get_attribute('data-tag')
                               for span in self.driver.find_elements_by_css_selector('section.tag-cloud-container span[data-tag]') }
                input_tags = recommend_tags & cloud_tags

                form = self.driver.find_element_by_css_selector('section.bookmark-detail-unit form')
                form_input = form.find_element_by_css_selector('#input_tag')
                form_input.clear()
                form_input.send_keys(' '.join(input_tags))
                form.submit()

                print('input_tags: {}'.format(input_tags))
                print('Completed: {}/{}'.format(i, len(edit_links)))
                print('-' * 80)
                self.sleep(0.5)
            except NoSuchElementException:
                pass


    def sleep(self, sec):
        time.sleep(sec)
        return self

def main():
    project_root = os.path.abspath(os.path.dirname(sys.argv[0]))
    with Tagger(PIXIV_ID, PASSWORD) as tagger:
        tagger.login().sleep(1.5)
        tagger.autotag()



if __name__ == '__main__':
    main()
