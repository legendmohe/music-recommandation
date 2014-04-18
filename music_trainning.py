#!/usr/bin/python
# coding: utf-8
import httplib
import json
import os
import sys
import subprocess
import time
import random
import threading
import urllib2
import threading
from datetime import datetime
import tornado.ioloop
import tornado.web

reload(sys)
sys.setdefaultencoding('utf-8')

def init_log_file():
    now = datetime.now()
    log_file_name = "music_%s_%s_%s.log" % (now.year, now.month, now.day)
    return open(log_file_name, "w")

def get_channcels():
    channel_json = urllib2.urlopen("http://www.douban.com/j/app/radio/channels").read()
    channels = json.loads(channel_json)["channels"]
    channels = [c for c in channels if 0 < int(c["channel_id"]) < 100]
    for channel in [(x["channel_id"], x['name']) for x in channels]:
        print channel[0], ":", channel[1]
    print "-"*50
    return channels

log_file = init_log_file()
channels = get_channcels()
lock = threading.Lock()
stop_playing = False
cur_music_url = ""
cur_channel = ""

def music_worker():
    global player, channels, lock, stop_playing, cur_music_url, cur_channel
    while True:
        if stop_playing:
            lock.acquire()

        channel = random.choice(channels)
        channel_id = str(channel['channel_id'])
        cur_channel = channel['name']
        print "current channel: ", cur_channel
        try:
            httpConnection = httplib.HTTPConnection('douban.fm')
            httpConnection.request('GET', '/j/mine/playlist?type=n&channel=' + channel_id)
            song = json.loads(httpConnection.getresponse().read())['song']
            cmd = r'D:\mpg123\mpg123 ' + song[0]['url']
            with open(os.devnull, 'w') as tempf:
                player = subprocess.Popen(cmd, stdout=tempf, stderr=tempf)
                cur_music_url = song[0]['url']
                print 'playing: ', cur_music_url
                player.wait()
        except Exception, e:
            print e


music_thread = threading.Thread(target = music_worker)
music_thread.setDaemon(True)
music_thread.start()


class NextHandler(tornado.web.RequestHandler):
    def get(self):
        global stop_playing, lock, player
        if stop_playing:
            stop_playing = False
            lock.release()
            self.write("resume")
        else:
            player.kill()
            self.write("next")


class PauseHandler(tornado.web.RequestHandler):
    def get(self):
        global stop_playing, lock, player
        if stop_playing is False:
            stop_playing = True
            lock.acquire()
            player.kill()
            self.write("pause")


class MarkHandler(tornado.web.RequestHandler):
    def get(self):
        global cur_music_url, cur_channel, log_file
        now = time.time()
        log_content = "%s|%s|%s|1" % (now, cur_channel, cur_music_url)
        log_file.write(log_content)
        self.write("mark:" + cur_channel + "\nurl:" +cur_music_url)


application = tornado.web.Application([
    (r"/next", NextHandler),
    (r"/pause", PauseHandler),
    (r"/mark", MarkHandler),
])


if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
