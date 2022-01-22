import requests
import re
from .CONFIG import TIMEZONE
from .Stream import Stream


class Hololive:
    hololive_url = 'https://schedule.hololive.tv/simple'

    def __init__(self):
        self.page_resources = None
        self.streams = []
        self.filtered_streams = []

    def scrape_raw(self):
        self.page_resources = requests.get(self.hololive_url, cookies=TIMEZONE)
        self.page_resources = self.page_resources.text.split('\n')
        self.page_resources = [i.replace(" ", "").replace("\r", "") for i in self.page_resources]
        body_index = self.page_resources.index('<divclass="holodulenavbar-text"style="letter-spacing:0.3em;">')
        self.page_resources = self.page_resources[body_index:]

    @staticmethod
    def get_title_keywords():
        f = open('./title_keywords.txt', 'r', encoding='utf-8')
        return f.read().splitlines()

    @staticmethod
    def get_name_keywords():
        f = open('./name_keywords.txt', 'r', encoding='utf-8')
        return f.read().splitlines()

    def filter(self):
        title_pattern = "|".join(self.get_title_keywords())
        streamer_pattern = "|".join(self.get_name_keywords())

        if not title_pattern:
            self.filtered_streams = [stream for stream in self.streams if re.search(streamer_pattern, stream.streamer, re.IGNORECASE)]
        elif not streamer_pattern:
            self.filtered_streams = [stream for stream in self.streams if re.search(title_pattern, stream.title, re.IGNORECASE)]
        else:
            self.filtered_streams = [stream for stream in self.streams if re.search(streamer_pattern, stream.streamer, re.IGNORECASE) or re.search(title_pattern, stream.title, re.IGNORECASE)]

        self.filtered_streams = [stream for stream in self.filtered_streams if (stream.is_upcoming() or stream.is_live()) and not stream.is_member_only()]

    def update(self):
        self.scrape_raw()
        f = open('./hololive_name.txt', 'r', encoding='utf-8')
        name_list = f.read().splitlines()
        regex_pair = {'date': r'^(0[1-9]|1[0-2])\/(0[1-9]|1\d|2\d|3[01])$',
                      'weekday': r'\([\u0080-\uFFFF]\)',
                      'time': r'^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$',
                      'url': r'(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])'}

        date = None
        _time = None
        url = None
        date_time = None

        for s in self.page_resources:

            for k, v in regex_pair.items():

                dummy = re.search(v, s)
                if dummy:

                    if k == 'date':
                        date = dummy.group()

                    elif k == 'time':
                        _time = dummy.group()
                        date_time = date + " " + _time

                    elif k == 'url':
                        url = dummy.group()

            if s in name_list:
                streamer = s
                if not self.duplicate_stream(url):
                    stream = Stream(start_time=date_time,
                                    streamer=streamer,
                                    url=url)
                    # print(stream)
                    self.streams.append(stream)

    def duplicate_stream(self, new_url):
        for stream in self.streams:
            if stream.url == new_url:
                return True
        return False