#!/usr/bin/python
# coding: utf-8

import pdb

import httplib
import json
import os
import sys
import subprocess
import time
import random
import threading
import signal
import urllib2
import threading
from datetime import datetime
import tornado.ioloop
import tornado.web


# http://stackoverflow.com/questions/17101502/how-to-stop-the-tornado-web-server-with-ctrlc
is_closing = False


def signal_handler(signum, frame):
    global is_closing
    is_closing = True


def try_exit():
    global is_closing
    if is_closing:
        # clean up here
        tornado.ioloop.IOLoop.instance().stop()


import channels_list

channels = channels_list.CHANNELS["type1"]
channels_groupby_type = {}
for channel in channels:
    channels_groupby_type[channel["name"]] = channel
cur_channel = random.choice(channels)

reload(sys)
sys.setdefaultencoding('utf-8')

def init_log_file():
    now = datetime.now()
    log_file_name = "music_%s_%s_%s.log" % (now.year, now.month, now.day)
    print "init log file: ", log_file_name
    log_file = open(log_file_name, "w")
    return log_file

log_file = init_log_file()
lock = threading.Lock()
stop_playing = False

def processMp3Address(src):
    res = src[13:-2] #  remove JsonCallBack and quotes
    song = eval(res)['songs'][0]
    url = song["url"]
    url = url[:url.index('/', 10) + 1]
    url = url + str(int(song["id"]) + 30000000) + ".mp3"
    # print "url:", url
    return url

def processCMD(song):
    cmd = 'mplayer -http-header-fields \"Cookie: pgv_pvid=9151698519; qqmusic_uin=12345678; qqmusic_key=12345678; qqmusic_fromtag=0;\" ' + song
    # print "cmd:", cmd
    return cmd

def music_worker():
    global player, channels, lock, stop_playing, cur_music_url, cur_channel
    while True:
        if stop_playing:
            lock.acquire()

        channel_id = str(cur_channel['id'])
        print "current channel: ", cur_channel['name']
        try:
            httpConnection = httplib.HTTPConnection('radio.cloud.music.qq.com')
            httpConnection.request('GET', '/fcgi-bin/qm_guessyoulike.fcg?start=-1&num=1&labelid=%s&jsonpCallback=MusicJsonCallback' % (channel_id, ))
            
            song = processMp3Address(httpConnection.getresponse().read())
            cmd = processCMD(song)
            with open(os.devnull, 'w') as tempf:
                player = subprocess.Popen(cmd, stdout=tempf, stderr=tempf)
                cur_music_url = song
                player.wait()
                # pdb.set_trace()
        except Exception, e:
            print e

music_thread = threading.Thread(target = music_worker)
music_thread.setDaemon(True)
music_thread.start()


class NextHandler(tornado.web.RequestHandler):
    def get(self):
        global stop_playing, lock, player, cur_channel, channels

        song_type = self.get_argument("type", None)
        if song_type is None:
            cur_channel = random.choice(channels)
        else:
            cur_channel = channels_groupby_type[song_type]
        if stop_playing:
            stop_playing = False
            lock.release()
        else:
            player.kill()
        self.write(cur_channel['name'])


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
        log_content = "%s|%s|%s|1\n" % (now, cur_channel['name'], cur_music_url)
        log_file.write(log_content)
        log_file.flush()
        self.write(log_content)


class ListHandler(tornado.web.RequestHandler):
    def get(self):
        global channels
        response = "\n".join([item["name"] for item in channels])
        self.write(response)


application = tornado.web.Application([
    (r"/next", NextHandler),
    (r"/pause", PauseHandler),
    (r"/mark", MarkHandler),
    (r"/list", ListHandler),
])
application.listen(8888)
signal.signal(signal.SIGINT, signal_handler)
tornado.ioloop.PeriodicCallback(try_exit, 100).start()
tornado.ioloop.IOLoop.instance().start()
