import math
import os
import random
import re
import sys
from _md5 import md5

from PyQt5.QtCore import QObject, QThreadPool, pyqtSlot, pyqtSignal, QModelIndex
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon

os.environ['PATH'] = os.path.dirname(__file__) + os.pathsep + os.environ['PATH']
import mpv
from config import config

def my_log(loglevel, component, message):
	print('[{}] {}: {}'.format(loglevel, component, message))




songLoadBegun = 1
songLoadInProgress = 2
songLoadFinished = 3


class playbackController(QObject):
	getSongHandle = pyqtSignal(object)
	updatePlayerUI = pyqtSignal(object, str)

	def __init__(self, networkWorker):
		super(playbackController, self).__init__()
		self.playQueueModel = QStandardItemModel()
		self.songLoaderThreads = QThreadPool()

		self.player = mpv.MPV(log_handler=my_log, loglevel='debug')
		self.player['prefetch-playlist'] = True
		self.player['gapless-audio'] = True
		self.player['force-seekable'] = True
		self.player['demuxer-max-back-bytes'] = 999999999
		self.player['cache-secs'] = 99999999.0
		self.player['demuxer-max-bytes'] = 99999999999
		self.player.observe_property('time-pos', self.updateProgressBar)
		self.player.observe_property('media-title', self.updateSongDetails)
		self.player.observe_property('core-idle', self.updateIdleState)
		self.player.observe_property('audio-params', self.watchAudioParams)
		self.player.observe_property('path', self.filenameChanged)

		self.playQueueModel.setHorizontalHeaderLabels(['Title', 'Artist', 'Album'])
		self.currentSong = None
		# signals

		self.salt = md5(os.urandom(100)).hexdigest()
		self.token = md5((config.password + self.salt).encode('utf-8')).hexdigest()

	def currentSongFullyLoaded(self):

		try:
			id = self.currentSong.data()['id']
			if self.songCache[id][0] == songLoadFinished:
				return True
			else:
				return False
		except KeyError:
			return False
		except AttributeError:
			return False
		except RuntimeError:
			return False


	def changeCurrentSong(self, newsong):
		if newsong == None:
			print('setting current song to None. Caller: {}'.format(sys._getframe().f_back.f_code.co_name))
		if self.currentSong:
			try:
				self.currentSong.setIcon(QIcon())
			except RuntimeError:
				pass
		self.currentSong = newsong
		if newsong:
			self.currentSong.setIcon(QIcon('icons/baseline-play-arrow.svg'))
			self.updatePlayerUI.emit(self.playQueueModel.indexFromItem(self.currentSong), 'scrollTo')

	def stop(self):
		self.changeCurrentSong(None)
		self.player.command('stop')

	def shufflePlayQueue(self):
		items = []
		currsong = self.currentSong.data()
		for item in range(self.playQueueModel.rowCount()):
			item = self.playQueueModel.item(item, 0).data()
			if not item['id'] == self.currentSong.data()['id']:
				items.append(item)
		random.shuffle(items)
		items.insert(0, currsong)
		self.clearPlayQueue(clearCache=False)
		self.addSongs(items)
		self.changeCurrentSong(self.playQueueModel.item(0, 0))
		self.syncMpvPlaylist()

	def playNow(self, allSongs, song):
		# replace the play queue with the album (allSongs), then play song from that album.
		# should assert that song is in allSongs
		self.player.command('stop')
		self.clearPlayQueue()
		self.addSongs(allSongs)
		self.filenameChanged("", self.buildUrlForSong(song))
		self.playSong(song)

	def clearPlayQueue(self, clearCache=True):
		self.playQueueModel.clear()
		if clearCache:
			self.songCache = {}
		self.playQueueModel.setHorizontalHeaderLabels(['Title', 'Artist', 'Album'])

	def addSongs(self, songs, afterCurrent=False):
		# pass in a list of song dicts from the subsonic api, not an album!
		print('adding {} songs to playqueue'.format(len(songs)))
		# print(songs)
		if afterCurrent and self.currentSong:
			row = self.playQueueModel.indexFromItem(self.currentSong).row() + 1
		else:
			row = None
		for item in songs:
			standardItems = []
			for key in ['title', 'artist', 'album']:
				try:
					standardItems.append(QStandardItem(item[key]))
				except KeyError:
					standardItems.append(QStandardItem('No {}'.format(key)))
			for standardItem in standardItems:
				standardItem.setData(item)
			if row:
				self.playQueueModel.insertRow(row, standardItems)
				print('inserting row for {}'.format(item['title']))
			else:
				self.playQueueModel.appendRow(standardItems)

	def syncMpvPlaylist(self):
		self.player.playlist_clear()
		try:
			index = self.playQueueModel.indexFromItem(self.currentSong).row() + 1
		except RuntimeError:
			print('syncing mpv playlist when playqueue cleared, bailing')
			return
		# add the next item and all those after it to the mpv playlist
		while True:
			song = self.playQueueModel.item(index, 0)
			if song:
				self.player.playlist_append(self.buildUrlForSong(song.data()))
				index += 1
			else:
				break

	def buildUrlForSong(self, song):
		return config.fqdn + '/rest/stream.view?f=json&v=1.15.0&c=' + \
			   config.appname + '&u=' + config.username + '&s=' + self.salt + \
			   '&t=' + self.token + '&id=' + song['id']

	def playSong(self, song):
		url = self.buildUrlForSong(song)
		print('playing {}'.format(url))
		self.player.play(url)
		self.player['pause'] = False
		self.syncMpvPlaylist()

	@pyqtSlot()
	def playNextSongExplicitly(self):
		self.player.playlist_next()

	# if self.getNextSong():
	# 	song = self.getNextSong()
	# 	self.changeCurrentSong(song)
	# 	self.beginSongLoad(song.data())
	# else:
	# 	# with no next song, either repeat (TODO) or stop.
	# 	self.player.command('stop')

	@pyqtSlot()
	def playPreviousSong(self):
		self.player.playlist_prev()

	# if self.getPreviousSong():
	# 	song = self.getPreviousSong()
	# 	self.changeCurrentSong(song)
	# 	self.beginSongLoad(song.data())
	# else:  # if at top of queue, restart song.
	# 	try:
	# 		self.player.seek(0, 'absolute')
	# 	except SystemError:
	# 		print('unable to seek to 0')

	@pyqtSlot(int)
	def setVolume(self, value):
		self.player.volume = value
		config.volume = value

	@pyqtSlot(QModelIndex)
	def playSongFromQueue(self, index):
		index = index.siblingAtColumn(0)
		song = self.playQueueModel.itemFromIndex(index)
		print('playing {} from queue click'.format(song.data()['title']))
		self.changeCurrentSong(song)
		self.beginSongLoad(song.data())

	def getPreviousSong(self):
		currentindex = self.playQueueModel.indexFromItem(self.currentSong)
		try:
			return self.playQueueModel.item(currentindex.row() - 1, 0)
		except AttributeError:
			return None

	def getNextSong(self):
		try:
			currentindex = self.playQueueModel.indexFromItem(self.currentSong)
		except RuntimeError:
			print('Unable to get index for current song')
			return None
		# print('got index for current song: {}'.format(currentindex.row()))
		try:
			return self.playQueueModel.item(currentindex.row() + 1, 0)
		except AttributeError:
			print('Unable to get index for next song')
			return None

	def updateProgressBar(self, _name, _value):
		try:
			total = self.currentSong.data()['duration']
		except RuntimeError:
			print('updateProgressBar here: currentsong has been deleted.')
			return
		except AttributeError:
			print('updateProgressBar here: no currentsong!')
			return
		value = self.player.time_pos  # Get the value direct from player to ensure not getting a
		# leftover from offPlayer
		duration = self.player.duration

		# print("progress: {}, percent: {}".format(value, percent))
		if value and duration:
			self.updatePlayerUI.emit(math.ceil(total), 'total')
			self.updatePlayerUI.emit(math.ceil(value), 'progress')

	# print('mpv pos ceil\'d: {}, max: {}'.format(math.ceil(value), self.currentSong.data()['duration']))

	def watchAudioParams(self, _name, params):
		print('rebuilding audio stat line')
		audioOutParams = {}
		trackList = {}
		try:
			trackList = self.player.track_list
			trackList = trackList[0]
			audioOutParams = self.player.audio_out_params
		except AttributeError:
			pass
		except IndexError:
			pass
		ret = ""
		if self.player.audio_codec_name:
			ret += self.player.audio_codec_name + " | "
		if trackList and 'demux-bitrate' in trackList:
			ret += str(int(trackList['demux-bitrate'] / 1000)) + 'kbps | '
		if trackList and 'demux-samplerate' in trackList:
			ret += str(trackList['demux-samplerate']) + 'hz -> '
		if audioOutParams and 'samplerate' in audioOutParams:
			ret += str(audioOutParams['samplerate']) + 'hz | '
		if params and 'hr-channels' in params:
			ret += str(params['hr-channels']) + ' | '
		self.updatePlayerUI.emit(ret, 'statusBar')

	def filenameChanged(self, _name, value):
		if value:
			print('MPV song changed. mpv path:')
			print(value)
			id = re.search(r'&id=(?P<id>\d+)$', value).group('id')
			print('found id {}'.format(id))
			if self.currentSong:
				if id == self.currentSong.data()['id']:
					print('no need to adjust currentSong')
					return
				try:
					nextid = self.getNextSong().data()['id']
					if id == nextid:
						self.changeCurrentSong(self.getNextSong())
						return
				except AttributeError:
					pass
			for n in range(self.playQueueModel.rowCount()):
				print(n)
				checkid = (self.playQueueModel.item(n, 0).data()['id'])
				print('checking against {} '.format(checkid))
				if checkid == id:
					print('this is it!')
					self.changeCurrentSong(self.playQueueModel.item(n, 0))
					return
			print('unable to find song in queue :(')

	@pyqtSlot(int)
	def setTrackProgress(self, position):
		try:
			print('seeking to {}'.format(position))
			self.player.command('seek', position, 'absolute+exact')
		except SystemError:
			pass

	def updateSongDetails(self, _name, value):
		# print('emitting update title')
		value = self.player.media_title
		self.updatePlayerUI.emit(value, 'title')

	def updateIdleState(self, _name, value):
		# print('player idle state: {}'.format(value))
		value = self.player.core_idle
		self.updatePlayerUI.emit(value, 'idle')

	@pyqtSlot(bool)
	@pyqtSlot()
	def playPause(self, clicked=False):
		if self.player['pause']:
			self.player['pause'] = False
		else:
			self.player['pause'] = True

	@pyqtSlot(str)
	def playbackControl(self, type):
		if type == 'playPause':
			self.playPause()
		elif type == "nextSong":
			self.playNextSongExplicitly()
		elif type == "prevSong":
			self.playPreviousSong()
