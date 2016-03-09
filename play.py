#!/usr/local/Cellar/python
# -*- coding: utf-8 -*-

# @Author: homeway
# @Link: http://homeway.me
# @Version: 15.03.17

import pygame
import pymongo
import shutil
import wget,threading,time,os,api
threads = []

STOP = 0
PLAYING = 1
PAUSE = 2

class MusicData(object):
	def set_music_info(self, info):
		return self.db.save(info)

	def get_music_info(self, sid):
		res = self.db.find_one({ 'sid': sid })
		if res:
			return res
		else:
			return False

	def get_play_list_next(self):
		res = self._db.play_list.find_one()
		if res:
			return self.cover_music_data(res)
		else:
			return False

	def get_music_from_play_list(self, sid):
		res = self._db.play_list.find_one({ 'sid': sid })
		if res:
			return self.cover_music_data(res)
		else:
			return False

	def del_music_from_play_list(self, sid):
		return self._db.play_list.remove({ 'sid': sid })


	def add_to_play_list(self, info):
		return self._db.play_list.save(info)

	def add_to_played_list(self, info):
		return self._db.played_list.save(info)
	
	def get_play_list(self, page, pagesize):
		musics = self._db.play_list.find().skip((page-1)*pagesize).limit(pagesize)
		res = []
		for music in musics:
			res.append( self.cover_music_data(music) )
		return res

	def cover_music_data(self, music):
		music['_id'] = str(music['_id'])
		music['duration'] = int(music['duration'])
		return music

	def get_played_list(self, page, pagesize):
		pass

class Play(MusicData):
	def __init__ (self, option):
		self.currentMusic = None
		self.db_option = option
		self.play_status = STOP
		self.need_to_pause = False # 暂停播放
		self.need_to_play = False # 继续播放
		self.need_to_next = False # 播放下一首
		self.next_song_count = 0
		self.music_option = {
			'frequence' : 44100,
			'bitsize' : -16,
			'channels' : 1,
			'buffer' : 2048,
		}
		self.music_info={
			'sid' : '',
			'name' : '',
			'md5' : '',
			'mp3Url' : '',
			'path' :'',
		}
		# connect to mongodb
		self._conn = pymongo.MongoClient( option['host'], option['port'] )
		self._db = self._conn[ option['db'] ]
		self.db = self._db.music
		# setting pygame
		pygame.mixer.init( self.music_option['frequence'], self.music_option['bitsize'], self.music_option['channels'], self.music_option['buffer'])
		pygame.mixer.music.set_volume(1)
	
	def status(self):
		return self.play_status

	def current_playing_music(self):
		if not self.currentMusic:
			m = self.get_play_list_next()
			if m:
				self.currentMusic = m
		if not self.currentMusic:
			return None
		return self.currentMusic

	# order music
	def order_music(self, music_info):
		res = {
			'success': False,
			'error': '',
		}
		m = self.get_music_from_play_list(music_info['sid'])
		if m:
			res['error'] = u'歌曲 [' + music_info['name'] + u'] 已经在点播列表中'
			return res
		MusicData.add_to_play_list(self, music_info)
		res['success'] = True
		return res

	def next_song(self, count):
		if self.next_song_count < count:
			self.next_song_count += 1
			return
		print 'Request to play next song is more than ', count, u', play next song.'
		self.next_song_count = 0
		self.need_to_next = True

	def move_to_played_list(self, sid):
		m = self.get_music_from_play_list(sid)
		if m:
			self.add_to_played_list(m)
		return self.del_music_from_play_list(sid)

	# play music
	def play_music(self, sid):
		self.need_to_next = False
		if self.play_status != STOP:
			if str(self.music_info['sid']) == str(sid) or str(sid) == '':
				self.need_to_play = True
				return
		item = threading.Thread( target=self.play_music_thread, args=( sid,), name="player" )
		threads.append( item )
		item.start()
		self.play_status = PLAYING
		self.need_to_play = False

	# play threading
	def play_music_thread(self,sid):
		music_info = MusicData.get_music_info(self, sid)
		if not music_info:
			music_info = self.search_music_info(sid)
		else:
			self.music_info=music_info
		# play now
		clock = pygame.time.Clock()
		try:
			print self.music_info['path']
			pygame.mixer.music.load(self.music_info['path'])
			print("Music file {} loaded!".format(self.music_info['path']))
		except pygame.error:
			print("File {} error! {}".format(self.music_info['path'], pygame.get_error()))
			return
		pygame.mixer.music.play()
		print 'start play ', self.music_info['sid']
		# 设置当前播放的音乐
		self.currentMusic = self.get_music_from_play_list(sid)
		while pygame.mixer.music.get_busy():
			clock.tick(30)
			if self.need_to_next:
				pygame.mixer.music.stop()
				self.need_to_next = False
				print 'start play next song'
			if self.need_to_pause:
				pygame.mixer.music.pause()
				self.need_to_pause = False
				self.play_status = PAUSE
				wait_to_play = True
				while wait_to_play:
					clock.tick(30)
					if self.need_to_play:
						wait_to_play = False
						pygame.mixer.music.unpause()
						self.need_to_play = False
						self.play_status = PLAYING

		self.move_to_played_list(sid)
		m = self.get_play_list_next()
		self.currentMusic = None
		if m:
			print 'Play next music from play-list:', m['sid']
			self.play_music(m['sid'])
		else:
			self.play_status = STOP

	# search by api and get info
	def search_music_info(self, sid):
		NetEase = api.NetEase()
		login = NetEase.login('username', 'password')#NetEase username, password
		music_data = NetEase.song_detail(sid)
		self.music_info['mp3Url'] = music_data[0]['mp3Url']
		self.music_info['name'] = music_data[0]['name']
		self.music_info['sid'] = music_data[0]['id']
		music_place = self.download_music(self.music_info['mp3Url'])
		if music_place:
			MusicData.set_music_info( self, self.music_info )
		else:
			return
	# download and move
	def download_music(self, url):
		abs_path = os.path.abspath('./')
		file_path = abs_path + '/music'
		if not os.path.exists( file_path ):
			try:
				os.makedirs( file_path )
			except:
				print '权限不足，无法创建目录...'
		else:
			pass
		# 下载并移动
		try:
			music = wget.download(url)
		except:
			print '下载出错...'
		
		try:
			dest = file_path+'/'+music
			shutil.move( music, dest)
			self.music_info['path'] = dest#'music/'+music
			return dest
		
		except:
			print '文件写入错误...'

	def set_volume(self, value):
		try:
			pygame.mixer.music.set_volume( float(value) )
			return value
		except:
			return False
		pass

	# 设置音量
	def setVolume(self, value):
		pygame.mixer.music.set_volume( float(value) )
		#pygame.mixer.music.set_volume(1)
		return value

	# 获取音量
	def getVolume(self):
		value = pygame.mixer.music.get_volume()
		return value
	

if __name__ == "__main__":
	option = {
		'host':'localhost',
		'port': 27017,
		'db':'MusicBox',   
	}
	play = Play(option)
	play.play_music(27731178)





