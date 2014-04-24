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
import urllib2
import threading
from datetime import datetime
import tornado.ioloop
import tornado.web

import channels_list

channels = channels_list.CHANNELS["type3"]

reload(sys)
sys.setdefaultencoding('utf-8')

def init_log_file():
    now = datetime.now()
    log_file_name = "music_%s_%s_%s.log" % (now.year, now.month, now.day)
    print "init log file: ", log_file_name
    log_file = open(log_file_name, "w")
    return log_file

# def get_channcels():
#     channel_json = urllib2.urlopen("http://www.douban.com/j/app/radio/channels").read()
#     channels = json.loads(channel_json)["channels"]
#     channels = [c for c in channels if 0 < int(c["channel_id"]) < 100]
#     for channel in [(x["channel_id"], x['name']) for x in channels]:
#         print channel[0], ":", channel[1]
#     print "-"*50
#     return channels

log_file = init_log_file()
# channels = get_channcels()
lock = threading.Lock()
stop_playing = False
cur_music_url = ""
cur_channel = ""

def processMp3Address(src):
    res = src[13:-2] #  remove JsonCallBack and quotes
    song = eval(res)['songs'][0]
    url = song["url"]
    url = url[:url.index('/', 10) + 1]
    url = url + str(int(song["id"]) + 30000000) + ".mp3"
    print "url:", url
    return url

def processCMD(song):
    cmd = 'mplayer -http-header-fields \'Cookie: pgv_pvid=9151698519; qqmusic_uin=12345678; qqmusic_key=12345678; qqmusic_fromtag=0;\' ' + song
    print "cmd:", cmd
    return cmd

def music_worker():
    global player, channels, lock, stop_playing, cur_music_url, cur_channel
    while True:
        if stop_playing:
            lock.acquire()

        channel = random.choice(channels)
        channel_id = str(channel['id'])
        cur_channel = channel_id
        print "current channel: ", channel['name']
        try:
            httpConnection = httplib.HTTPConnection('radio.cloud.music.qq.com')
            httpConnection.request('GET', '/fcgi-bin/qm_guessyoulike.fcg?start=-1&num=1&labelid=%s&jsonpCallback=MusicJsonCallback' % (channel_id, ))
            
            song = processMp3Address(httpConnection.getresponse().read())
            cmd = processCMD(song)
            with open(os.devnull, 'w') as tempf:
                player = subprocess.Popen(cmd, stdout=tempf, stderr=tempf)
                cur_music_url = song
                print 'playing: ', cur_music_url
                player.wait()
                # pdb.set_trace()
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
        log_file.flush()
        self.write(log_content)


application = tornado.web.Application([
    (r"/next", NextHandler),
    (r"/pause", PauseHandler),
    (r"/mark", MarkHandler),
])


if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
