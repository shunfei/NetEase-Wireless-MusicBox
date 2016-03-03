#!/usr/local/Cellar/python
# -*- coding: utf-8 -*-

# @Author: homeway
# @Link: http://homeway.me
# @Version: 15.03.17

import tornado.auth
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.web
import os.path
import json
import time
import random

# upload
import shutil
import os

#url
import urlparse

import logging
#import Image 
#import exifread 
#import tempfile

# cookie_secret
import base64 
import uuid  
import hashlib 

# mongodb
# import pymongo
# session
#from mongosion import Session
#import session

from tornado.escape import json_encode
from tornado.options import define, options


#some global information like session

import play
import api

# 先初始化播放器
global player
# mongodb数据库
option = {
    'host':'localhost',
    'port': 27017,
    'db':'MusicBox',   
}
player = play.Play(option)

define("port", default=80, help="run on the given port", type=int)
define("db", default="MusicBox", help="database name", type=str)
define("db_host", default='localhost', help="database host", type=str)
define("db_port", default=27017, help="database port", type=int)
define("db_user", default='root', help="database user", type=str)
define("db_pwd", default='xiaocao', help="database password", type=str) 

NetEase = api.NetEase()
login = NetEase.login('username', 'password')

class Application(tornado.web.Application):
    '''setting || main || router'''
    def __init__(self):
        handlers = [
            #for html
            (r"/", MainHandler),
            (r"/song.html", GetSongHandler),
            (r"/album.html", GetAlbumHandler),
            (r"/play-list.html", GetPlayListHandler),
            
            #for ajax
            (r"/ajaxSearch", AjaxSearchHandler),
            (r"/ajaxGetSong", AjaxGetSongHandler),
            (r"/ajaxAlbum", AjaxGetAlbumHandler),
            (r"/ajaxLogin", AjaxLoginHandler),
            (r"/ajaxOrderMusic", AjaxOrderMusicHandler),
            (r"/ajaxPlayMusic", AjaxPlayMusicHandler),
            (r"/ajaxPauseMusic", AjaxPauseMusicHandler),
            (r"/ajaxPlayNextMusic", AjaxPlayNextMusicHandler),
            (r"/ajaxNewAlbums", AjaxNewAlbumsHandler),
            (r"/ajaxHotSong", AjaxHotSongHandler),
            (r"/ajaxSetVolume", AjaxSetVolumeHandler),
        ] 
        
        settings = dict(
            cookie_secret=base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes),
            base_path=os.path.join(os.path.dirname(__file__), ""),
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=False,
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)


################################## html ############################################

class MainHandler(tornado.web.RequestHandler):
    def initialize(self):
        '''database init'''
        self.sid = self.get_secure_cookie("sid")
        #self.data = session.get(self.sid)
        #self.set_secure_cookie("sid",self.data['_id'])
        
    def get(self):
        self.set_header("Accept-Charset", "utf-8")
        NetEase.refresh()
        new_albums = NetEase.artists('4292')
        self.render("index.html", title="homeway|share", base_url=base_url, data=new_albums[0])

class GetPlayListHandler(tornado.web.RequestHandler):
    def initialize(self):
        pass
    def get(self):
        self.set_header("Accept-Charset", "utf-8")
        res = {}
        res['current'] = player.current_playing_music()
        # print res['current']
        res['list'] = player.get_play_list(1, 500)
        # self.write( tornado.escape.json_encode(res) )
        self.render("play-list.html", title="homeway|share", data=res)

class GetSongHandler(tornado.web.RequestHandler):
    def initialize(self):
    	pass
    def get(self):
        self.set_header("Accept-Charset", "utf-8")
        NetEase.refresh()
        req = { 'sid':self.get_argument("sid") } 
        res = NetEase.song_detail(  req['sid'] )
        #self.write( tornado.escape.json_encode(res) )
        self.render("song.html", title="homeway|share", data=res)

class GetAlbumHandler(tornado.web.RequestHandler):
    def initialize(self):
    	pass
    def get(self):
        self.set_header("Accept-Charset", "utf-8")
        NetEase.refresh()
        req = { 'aid':self.get_argument("aid") } 
        res = NetEase.album(  req['aid'] )
        #self.write( tornado.escape.json_encode(res) )
        self.render("album.html", title="homeway|share", data=res)

################################## ajax ############################################
#搜索信息
class AjaxSearchHandler(tornado.web.RequestHandler):
    def initialize(self):
        '''database init'''
        self.sid = self.get_secure_cookie("sid")
        #self.data = session.get(self.sid)
        #self.set_secure_cookie("sid",self.data['_id'])
    def get(self):
    	self.write( tornado.escape.json_encode( {'result': False, 'info': '拒绝GET请求！！' } ) )
    def post(self):
        self.set_header("Accept-Charset", "utf-8")
        NetEase.refresh()
        req = { 'key':self.get_argument("key") } 
        res = NetEase.search(  req['key'] )
        self.write( tornado.escape.json_encode(res['result']) )

# 点播音乐
class AjaxOrderMusicHandler(tornado.web.RequestHandler):
    def initialize(self):
        '''database init'''
        self.sid = self.get_secure_cookie("sid")
    def get(self):
        self.write( tornado.escape.json_encode( {'result': False, 'info': '拒绝GET请求！！' } ) )
    def post(self):
        self.set_header("Accept-Charset", "utf-8")
        req = {
            'sid':self.get_argument("sid"),
            'url':self.get_argument("url"),
            'name':self.get_argument("name"),
            'duration':self.get_argument("duration"),
            'artists':self.get_argument("artists"),
            'album_pic':self.get_argument("album_pic"),
            'album_name':self.get_argument("album_name"),
        }
        ok = player.order_music( req )
        self.write( tornado.escape.json_encode( {'result': ok['success'], 'info': ok['error'] } ) )


# 播放音乐
class AjaxPlayMusicHandler(tornado.web.RequestHandler):
    def initialize(self):
        '''database init'''
        self.sid = self.get_secure_cookie("sid")
        #self.data = session.get(self.sid)
        #self.set_secure_cookie("sid",self.data['_id'])
    def get(self):
    	self.write( tornado.escape.json_encode( {'result': False, 'info': '拒绝GET请求！！' } ) )
    def post(self):
        self.set_header("Accept-Charset", "utf-8")
        req = { 'sid':self.get_argument("sid"), 'url':self.get_argument("url"), } 
        if req['sid'] == '':
            m = player.get_play_list_next()
            if m:
                req['sid'] = m['sid']
        player.play_music( req['sid'] )
        self.write( tornado.escape.json_encode( {'result': True, 'info': 'play now...！！' } ) )

# 播放下一首音乐
class AjaxPlayNextMusicHandler(tornado.web.RequestHandler):
    def initialize(self):
        '''database init'''
        self.sid = self.get_secure_cookie("sid")
    def get(self):
        self.write( tornado.escape.json_encode( {'result': False, 'info': '拒绝GET请求！！' } ) )
    def post(self):
        self.set_header("Accept-Charset", "utf-8")
        res = {'result': True, 'info': ''}
        player.next_song( 5 )
        self.write( tornado.escape.json_encode( res ) )


# 暂停播放音乐
class AjaxPauseMusicHandler(tornado.web.RequestHandler):
    def initialize(self):
        '''database init'''
        self.sid = self.get_secure_cookie("sid")
    def get(self):
        self.write( tornado.escape.json_encode( {'result': False, 'info': '拒绝GET请求！！' } ) )
    def post(self):
        self.set_header("Accept-Charset", "utf-8")
        res = {'result': True, 'info': ''}
        if player.play_status == play.PLAYING:
            player.need_to_pause = True
            print u'暂停播放音乐'
        self.write( tornado.escape.json_encode( res ) )

# 登录网易云
class AjaxLoginHandler(tornado.web.RequestHandler):
    def initialize(self):
        '''database init'''
        self.sid = self.get_secure_cookie("sid")
        #self.data = session.get(self.sid)
        #self.set_secure_cookie("sid",self.data['_id'])
    def post(self):
    	self.write( tornado.escape.json_encode( {'result': False, 'info': '拒绝GET请求！！' } ) )
    def get(self):
        self.set_header("Accept-Charset", "utf-8")
        NetEase.refresh()
        req = { 'user':self.get_argument("user"), 'pass':self.get_argument("pass") } 
        res = NetEase.login(  req['user'], req['pass'] )
        self.write( tornado.escape.json_encode(res['profile']) )
# 获取音乐信息
class AjaxGetSongHandler(tornado.web.RequestHandler):
    def initialize(self):
        '''database init'''
        self.sid = self.get_secure_cookie("sid")
        #self.data = session.get(self.sid)
        #self.set_secure_cookie("sid",self.data['_id'])
    def post(self):
    	self.write( tornado.escape.json_encode( {'result': False, 'info': '拒绝GET请求！！' } ) )
    def get(self):
        self.set_header("Accept-Charset", "utf-8")
        NetEase.refresh()
        req = { 'sid':self.get_argument("sid") } 
        res = NetEase.song_detail( req['sid'] )
        self.write( tornado.escape.json_encode(res) )

class AjaxGetAlbumHandler(tornado.web.RequestHandler):
    def initialize(self):
        '''database init'''
        self.sid = self.get_secure_cookie("sid")
        #self.data = session.get(self.sid)
        #self.set_secure_cookie("sid",self.data['_id'])
    def post(self):
    	self.write( tornado.escape.json_encode( {'result': False, 'info': '拒绝GET请求！！' } ) )
    def get(self):
        self.set_header("Accept-Charset", "utf-8")
        NetEase.refresh()
        req = { 'aid':self.get_argument("aid") } 
        res = NetEase.album(  req['aid'] )
        self.write( tornado.escape.json_encode(res) )
# 调节音量
class AjaxSetVolumeHandler(tornado.web.RequestHandler):
    def initialize(self):
        '''database init'''
        self.sid = self.get_secure_cookie("sid")
    def get(self):
        self.write( tornado.escape.json_encode( {'result': False, 'info': '拒绝GET请求！！' } ) )
    def post(self):
        self.set_header("Accept-Charset", "utf-8")
        req = { 'value': self.get_argument("value") }
        res = player.setVolume( req['value'] )
        self.write( tornado.escape.json_encode( {'result': True, 'info': 'success！！' } ) )
# 获取最新的专辑
class AjaxNewAlbumsHandler(tornado.web.RequestHandler):
    def initialize(self):
        '''database init'''
        self.sid = self.get_secure_cookie("sid")
        #self.data = session.get(self.sid)
        #self.set_secure_cookie("sid",self.data['_id'])
    def get(self):
    	self.write( tornado.escape.json_encode( {'result': False, 'info': '拒绝GET请求！！' } ) )
    def post(self):
        self.set_header("Accept-Charset", "utf-8")
        NetEase.refresh()
        req = { 'offset': self.get_argument("offset"), 'limit': self.get_argument("limit") }
        res = NetEase.new_albums( req['offset'],req['limit'] )
        self.write( tornado.escape.json_encode(res) )
# 获取最热歌单
class AjaxHotSongHandler(tornado.web.RequestHandler):
    def initialize(self):
        '''database init'''
        self.sid = self.get_secure_cookie("sid")
        #self.data = session.get(self.sid)
        #self.set_secure_cookie("sid",self.data['_id'])
    def get(self):
        self.write( tornado.escape.json_encode( {'result': False, 'info': '拒绝GET请求！！' } ) )
    def post(self):
        self.set_header("Accept-Charset", "utf-8")
        NetEase.refresh()
        req = { 'offset': self.get_argument("offset"), 'limit': self.get_argument("limit") }
        res = NetEase.top_songlist( req['offset'],req['limit'] )
        self.write( tornado.escape.json_encode(res) )

def base_url(path):
    return "http://127.0.0.1/"+path

def main():
    tornado.options.parse_command_line()

    global player
    option['db'] = options['db']
    option['host'] = options['db_host']
    option['port'] = options['db_port']
    player = play.Play(option)
    
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main() 

