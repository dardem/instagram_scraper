import urllib.request
import re
import datetime
import pandas as pd
from selenium import webdriver
import os
import platform

from settings.general import BROWSER_PATH


class PostsParser:

    def parse_number(self, number):
        if (number[-1].isdigit()) & (number.find('.') == -1) & (number.find(',') == -1):
            return int(number)
        if number[-1].isdigit():
            return int(number.replace(',', ""))
        if number[-1] == 'k':
            return float(number[:-1]) * 10**3
        if number[-1] == 'm':
            return float(number[:-1]) * 10**6
        return -1

    def parse_post_text(self, post_content):
        start_pos = post_content.find('text')
        start_pos += len('text') + 3
        end_pos = start_pos
        for el in post_content[start_pos:]:
            if el == '}':
                break
            end_pos += 1

        return post_content[start_pos:end_pos-1]


    def parse_post_hashtags(self, text):
        hashtags = ''
        for m in re.finditer('#', text):
            start_pos = m.end()
            end_pos = start_pos
            for el in text[start_pos:]:
                if (not el.isdigit()) & (not el.isalpha()) & (el != '_'):
                    break

            hashtags += (text[start_pos:end_pos]) + ';'
        return hashtags


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


    def parse_post_shortcode(self, post_content):
        start_pos = post_content.find('shortcode')
        start_pos += len('shortcode') + 3
        end_pos = start_pos
        for el in post_content[start_pos:]:
            if el == '"':
                break
            end_pos += 1

        return post_content[start_pos:end_pos]


    def parse_content_post_likes(self, content_post):
        end_pos = content_post.find('Likes')
        end_pos -= 2
        start_pos = end_pos
        while (content_post[start_pos].isdigit()) | (content_post[start_pos] == 'm') | (content_post[start_pos] == 'k') | (content_post[start_pos] == ','):
            start_pos -=1
        return self.parse_number(content_post[start_pos+1:end_pos+1])


    def parse_content_post_owner(self, content_post):
        search_pos = re.search('<meta content="[\d]+[,.]?[\d]*[mk]? Likes, [\d]+[,.]?[\d]*[mk]? Comments (.*)\(@', content_post).span()[1]
        start_pos = search_pos
        end_pos = start_pos
        for el in content_post[start_pos:]:
            if (not el.isalpha()) & (not el.isdigit()) & (el != '_') & (el != '.'):
                break
            end_pos += 1

        return content_post[start_pos:end_pos]


    def parse_content_owner_followers(self, content_owner):
        end_pos = content_owner.find('Followers')
        end_pos -= 2
        start_pos = end_pos
        while (content_owner[start_pos] != ' ') & (content_owner[start_pos] != '"'):
            start_pos -= 1
        return self.parse_number(content_owner[start_pos+1:end_pos+1])


    def parse_content_owner_number_posts(self, content_owner):
        end_pos = content_owner.find('Posts')
        end_pos -= 2
        start_pos = end_pos
        while (content_owner[start_pos] != ' ') & (content_owner[start_pos] != '"'):
            start_pos -= 1
        return self.parse_number(content_owner[start_pos + 1:end_pos+1])


    def save_batch(self, df, tag):
        if not os.path.isdir('data/' + tag):
            os.makedirs('data/' + tag)

        df.drop(['content', 'shortcode'], axis=1).to_csv('data/' + tag + '/' + str(df.iloc[0]['datetime']) + ' -- ' + str(df.iloc[-1]['datetime']) + '.csv')


    def write_log(self, mess):
        with open('log/log.txt', 'a') as f:
            f.write(mess)


    def parse_urls(self, tag, from_top, start_index=0):

        if not os.getcwd() in os.get_exec_path():
            print('adding path')
            if platform.system() == "Windows":
                os.environ["PATH"] = os.environ["PATH"] + ";" + os.getcwd()
            else:
                os.environ["PATH"] = os.environ["PATH"] + ":" + os.getcwd()

        if not os.path.isdir('log'):
            os.mkdir('log')
            f = open('log/log.txt', "w+")
            f.write(str(datetime.datetime.now()) + ': parse for tag ' + tag + ' is started.')
            f.close()

        urls = [line.rstrip('\n') for line in open('urls/' + tag + '/urls.txt')]

        count_posts = 0
        posts_info = []
        curr_post_count = 0
        df = pd.DataFrame(
            columns=['content', 'text', 'hashtags', 'datetime', 'shortcode', 'likes', 'owner', 'owner_followers',
                     'owner_number_posts'])

        if not from_top:
            count_urls = start_index
            urls = urls[start_index:]
        else:
            count_urls = -1
            urls = ["https://www.instagram.com/explore/tags/" + tag + "/"] + urls

        for url in urls:
            count_urls += 1
            with open('urls/' + tag + '/last_parsed_url_index.txt', 'w+') as f:
                f.write(str(count_urls))

            driver = webdriver.Firefox(firefox_profile=BROWSER_PATH)
            driver.get(url)
            contents = driver.page_source
            contents_text = contents
            driver.quit()

            posts_positions = []

            for m in re.finditer('{"node":{"comments_disabled"', contents_text):
                posts_positions.append({'start': m.start(), 'end': m.end()})
                count_posts += 1

            self.write_log(str(datetime.datetime.now()) + ' ' + str(count_urls) + ': Total number of posts on the page: ' + str(count_posts) + '\n')

            if len(posts_positions) == 0:
                continue

            curr = posts_positions[0]

            for next in posts_positions[1:]:
                try:
                    post_content = contents_text[curr['start']: next['start']]
                    posts_info.append({'content': post_content,
                                       'text': self.parse_post_text(post_content),
                                       'hashtags': '',
                                       'datetime': self.parse_post_date(post_content),
                                       'shortcode': self.parse_post_shortcode(post_content),
                                       'likes': 0,
                                       'owner': '',
                                       'owner_followers': 0,
                                       'owner_number_posts': 0})
                    post = posts_info[-1]
                    contents_post = str(
                        urllib.request.urlopen("https://www.instagram.com/p/" + post['shortcode']).read())
                    post['likes'] = self.parse_content_post_likes(contents_post)
                    post['owner'] = self.parse_content_post_owner(contents_post)
                    # print(post['owner'])
                    content_owner = str(urllib.request.urlopen("https://www.instagram.com/" + post['owner']).read())
                    post['owner_followers'] = self.parse_content_owner_followers(content_owner)
                    post['owner_number_posts'] = self.parse_content_owner_number_posts(content_owner)

                    curr = next
                    curr_post_count += 1

                    df_post = pd.DataFrame([post])
                    df = df.append(df_post, ignore_index=True)
                except Exception as e:
                    self.write_log(str(datetime.datetime.now()) + ' ' + str(e) + '\n')
                    curr = next

            if curr_post_count >= 100:
                self.save_batch(df, tag)

                df = pd.DataFrame(
                    columns=['content', 'text', 'hashtags', 'datetime', 'shortcode', 'likes', 'owner',
                             'owner_followers',
                             'owner_number_posts'])
                curr_post_count = 0


#post_parser = PostsParser()
#post_parser.parse_urls('nivea', True)
