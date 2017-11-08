# -*- coding: utf-8 -*-
import json
import sys
import time
import re

import requests


class Tws(object):

    def __init__(self):
        # self.server_url = "https://punyapat.org/web/tech/lexto/ws.php"
        self.server_url = "http://127.0.0.1/web/tech/lexto/ws.php"
        requests.packages.urllib3.disable_warnings()

    def word_segment(self,sentence):
        # replace double quote with single-quote
        sentence = sentence.replace('"',"'")
        sentence = re.sub(pattern="\s*",repl="",string=sentence)

        # measure time used
        start = time.time()

        # eg. {"time":"your message"}
        r = requests.post(self.server_url, data=('{"text":"' + sentence + '"}').encode('utf-8'),verify=False)

        stop = time.time()

        if r.status_code == 200:
            j_output = json.loads(r.text)
            # sys.stdout.write('.')
            # sys.stdout.flush()
            return j_output
        else:
            # print "error input=%s status=%d reason=%s output=%s" % (sentence, r.status_code, r.reason, r.text)
            # print "error output=%s" % (r.text)
            return []

if __name__ == '__main__':
    result = Tws().word_segment(unicode('ทดสอบตัดคำไทยดูว่าแม่นไหม','utf-8'))
    print("|".join(result))
