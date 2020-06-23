import urllib.request
from bs4 import BeautifulSoup
import re
import datetime
import pandas as pd
from selenium import webdriver
import os
import platform
import time
import shutil

from settings.general import BROWSER_PATH


class KeyExtractor:
    def parse_content_js_script(self, content):
        start_pos = content.find('TagPageContainer.js') + len('TagPageContainer.js') + 1
        end_pos = start_pos
        for el in content[start_pos:]:
            if el == '.':
                break
            end_pos += 1

        return content[start_pos:end_pos]


    def parse_content_end_cursor(self, content):
        start_pos_ = content.find('"end_cursor"')
        start_pos  = start_pos_ + len('"end_cursor"') + 2
        end_pos = start_pos
        for el in content[start_pos:]:
            if el == '}':
                break
            end_pos += 1

        return start_pos_, content[start_pos:end_pos - 1]


    def parse_js_queryID(self, js):
        start_pos = js.find('tagMedia.byTagName.get(t).pagination},queryId')
        start_pos += len('tagMedia.byTagName.get(t).pagination},queryId') + 2
        end_pos = start_pos
        for el in js[start_pos:]:
            if el == '"':
                break
            end_pos += 1

        return js[start_pos:end_pos]


    def save_page_url(self, query, tag):
        if not os.path.isdir('urls'):
            os.mkdir('urls')

        if not os.path.isdir('urls/'+tag):
            os.mkdir('urls/'+tag)

        if not os.path.isfile('urls/' + tag + '/urls.txt'):
            f = open('urls/' + tag + '/urls.txt', 'w+')
            f.write(query + '\n')
            f.close()
        else:
            f = open('urls/' + tag + '/urls.txt', 'a')
            f.write(query + '\n')
            f.close()


    def parse_post_date(self, post_content):
        start_pos = post_content.find('taken_at_timestamp')
        start_pos += len('taken_at_timestamp') + 2
        end_pos = start_pos
        for el in post_content[start_pos:]:
            if el == ',':
                break
            end_pos += 1

        timestamp = int(post_content[start_pos:end_pos])

        return datetime.datetime.fromtimestamp(timestamp)


    def get_first_date(self, urls_file):
        urls = [line.rstrip('\n') for line in open(urls_file)]
        for url in urls:
            driver = webdriver.Firefox(firefox_profile=BROWSER_PATH)
            driver.get(url)
            contents = driver.page_source
            contents_text = contents
            driver.quit()

            posts_positions = []

            for m in re.finditer('{"node":{"comments_disabled"', contents_text):
                posts_positions.append({'start': m.start(), 'end': m.end()})

            if len(posts_positions) != 0:
                break

        post_content = contents_text[posts_positions[0]['start']: posts_positions[1]['start']]
        return self.parse_post_date(post_content)


    def get_last_date(self, urls_file):
        urls = [line.rstrip('\n') for line in open(urls_file)]

        for url in urls[::-1]:
            driver = webdriver.Firefox(firefox_profile=BROWSER_PATH)
            driver.get(url)
            contents = driver.page_source
            contents_text = contents
            driver.quit()

            posts_positions = []

            for m in re.finditer('{"node":{"comments_disabled"', contents_text):
                posts_positions.append({'start': m.start(), 'end': m.end()})

            if len(posts_positions) != 0:
                break

        post_content = contents_text[posts_positions[-2]['start']: posts_positions[-1]['start']]
        return self.parse_post_date(post_content)


    def parse_insta_pages(self, tag, max_amount, download_recent=True):
        try:
            if not os.getcwd() in os.get_exec_path():
                if platform.system() == "Windows":
                    os.environ["PATH"] = os.environ["PATH"] + ";" + os.getcwd()
                else:
                    os.environ["PATH"] = os.environ["PATH"] + ":" + os.getcwd()

            contents = urllib.request.urlopen("https://www.instagram.com/explore/tags/" + tag + "/").read()

            js_script = self.parse_content_js_script(str(contents))

            soup = BeautifulSoup(contents, 'html.parser')

            if not download_recent:
                f = open('urls/' + tag + '/urls.txt', 'r')
                urls = [line.rstrip('\n') for line in f]
                count_urls = len(urls)
                query = urls[-1]

                driver = webdriver.Firefox(firefox_profile=BROWSER_PATH)
                driver.get(
                    query)  # urllib.request.urlopen('https://www.instagram.com/graphql/query/?query_hash=' + queryID + '&variables=%7B%22tag_name%22%3A%22' + tag + '%22%2C%22first%22%3A' + str(12) + '%2C%22after%22%3A%22' + end_cursor + '%22%7D').read()

                contents = driver.page_source
                contents = driver.page_source

                driver.quit()
                f.close()
            else:
                if not os.path.isdir('urls/' + tag):
                    os.mkdir('urls/' + tag)

                count_urls = 0

                if os.path.isfile('urls/' + tag + '/last_parsed_url_index.txt'):
                    with open('urls/' + tag + '/last_parsed_url_index.txt', 'w+') as f:
                        f.write('0')

                if not os.path.isdir('urls/' + tag + '/backups'):
                    os.mkdir('urls/' + tag + '/backups')
                if os.path.isfile('urls/' + tag + '/urls.txt'):
                    date_from = self.get_first_date('urls/' + tag + '/urls.txt')
                    date_to   = self.get_last_date('urls/' + tag + '/urls.txt')
                    shutil.move('urls/' + tag + '/urls.txt', 'urls/' + tag + '/backups/' + str(date_from) + ' -- ' + str(date_to) + '.txt')

                query = "https://www.instagram.com/explore/tags/" + tag + "/"

            while count_urls < max_amount:
                time.sleep(5)
                print(contents)

                start_pos, end_cursor = self.parse_content_end_cursor(str(contents))
                if start_pos == -1:
                    driver = webdriver.Firefox(firefox_profile=BROWSER_PATH)
                    driver.get(
                        query)  # urllib.request.urlopen('https://www.instagram.com/graphql/query/?query_hash=' + queryID + '&variables=%7B%22tag_name%22%3A%22' + tag + '%22%2C%22first%22%3A' + str(12) + '%2C%22after%22%3A%22' + end_cursor + '%22%7D').read()

                    contents = driver.page_source
                    contents = driver.page_source

                    driver.quit()
                    continue

                contents_js = urllib.request.urlopen(
                    "https://www.instagram.com/static/bundles/base/TagPageContainer.js/" + js_script + ".js").read()
                queryID = self.parse_js_queryID(str(contents_js))

                query = 'https://www.instagram.com/graphql/query/?query_hash=' + queryID + '&variables=%7B%22tag_name%22%3A%22' + tag + '%22%2C%22first%22%3A' + str(
                    12) + '%2C%22after%22%3A%22' + end_cursor + '%22%7D'
                self.save_page_url(query, tag)
                count_urls += 1


                driver = webdriver.Firefox(firefox_profile=BROWSER_PATH)
                driver.get(
                    query)  # urllib.request.urlopen('https://www.instagram.com/graphql/query/?query_hash=' + queryID + '&variables=%7B%22tag_name%22%3A%22' + tag + '%22%2C%22first%22%3A' + str(12) + '%2C%22after%22%3A%22' + end_cursor + '%22%7D').read()

                contents = driver.page_source
                contents = driver.page_source

                driver.quit()

        except Exception as e:
            self.save_page_url(query, tag)
            print(e)
