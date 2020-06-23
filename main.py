from tools.key_extractor import KeyExtractor
from tools.data_parsing import PostsParser
from tools import write_log
from settings.general import TAGS

for tag in TAGS:
    mess = 'The parsing for tag: #' + tag + ' is started.'
    print(mess)
    write_log(mess)

    key_exctactor = KeyExtractor()
    key_exctactor.parse_insta_pages(tag, 50, True)

    post_parser = PostsParser()
    post_parser.parse_urls(tag, True)
