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


class playbackController(QObject):
	updatePlayerUI = pyqtSignal(object, str)

	def __init__(self, networkWorker):
		super(playbackController, self).__init__()
		self.playQueueModel = QStandardItemModel()
		self.songLoaderThreads = QThreadPool()

		self.player = mpv.MPV(log_handler=my_log, loglevel='info')
		self.player['prefetch-playlist'] = True
		self.player['gapless-audio'] = True
		self.player['force-seekable'] = True
		self.player['demuxer-max-back-bytes'] = 999999999
		self.player['cache-secs'] = 99999999.0
		self.player['demuxer-max-bytes'] = 99999999999
		self.player.observe_property('time-pos', self.updateProgressBar)
		self.player.observe_property('media-title', self.updateSongDetails)
		self.player.observe_property('core-idle', self.updateIdleState)
		self.player.register_event_callback(self.mpvEventHandler)
		self.player.observe_property('path', self.mpvUrlChanged)

		self.playQueueModel.setHorizontalHeaderLabels(['Title', 'Artist', 'Album'])
		self.currentSong = None

		self.salt = md5(os.urandom(100)).hexdigest()
		self.token = md5((config.password + self.salt).encode('utf-8')).hexdigest()


	def setCurrentSong(self, newsong):
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
		self.setCurrentSong(None)
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
		self.setCurrentSong(self.playQueueModel.item(0, 0))
		self.syncMpvPlaylist()

	def playNow(self, allSongs, song):
		# replace the play queue with the album (allSongs), then play song from that album.
		# should assert that song is in allSongs
		self.player.command('stop')
		self.clearPlayQueue()
		self.addSongs(allSongs, song)
		self.mpvUrlChanged("", self.buildUrlForSong(song))
		self.playSong(song)

	def clearPlayQueue(self, clearCache=True):
		self.playQueueModel.clear()
		if clearCache:
			self.songCache = {}
		self.playQueueModel.setHorizontalHeaderLabels(['Title', 'Artist', 'Album'])

	def addSongs(self, songs, currentSong=None, afterCurrent=False):
		# pass in a list of song dicts from the subsonic api, not an album!
		print('adding {} songs to playqueue'.format(len(songs)))
		# print(songs)
		currentSongStandardObject = None
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
			if currentSong and currentSong['id'] == item['id']:
				currentSongStandardObject = standardItems[0]
		if currentSongStandardObject:
			self.setCurrentSong(currentSongStandardObject)
		self.syncMpvPlaylist()

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
		if not self.currentSong:
			return
		try:
			self.player.playlist_next()
		except SystemError:
			if config.repeatList:
				self.playSongFromQueue(self.playQueueModel.index(0, 0))
			else:
				self.player.command('stop')

	# if self.getNextSong():
	# 	song = self.getNextSong()
	# 	self.changeCurrentSong(song)
	# 	self.beginSongLoad(song.data())
	# else:
	# 	# with no next song, either repeat (TODO) or stop.
	# 	self.player.command('stop')

	@pyqtSlot()
	def playPreviousSong(self):
		if not self.currentSong:
			return
		song = self.getPreviousSong().data()
		if song:
			self.playSong(song)
		else:
			self.player.seek(0, 'absolute')

	@pyqtSlot(int)
	def setVolume(self, value):
		self.player.volume = value
		config.volume = value

	@pyqtSlot(QModelIndex)
	def playSongFromQueue(self, index):
		index = index.siblingAtColumn(0)
		song = self.playQueueModel.itemFromIndex(index)
		print('playing {} from queue click'.format(song.data()['title']))
		self.setCurrentSong(song)
		self.playSong(song.data())

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

	def mpvEventHandler(self, event):
		if event['event_id'] == 8:  # file-loaded
			self.rebuildAudioStats()
		elif event['event_id'] == 7:
			self.mpvFileEnded(event)

	def rebuildAudioStats(self):
		print('rebuilding audio stat line')
		audioOutParams = {}
		trackList = {}
		try:
			trackList = self.player.track_list
			if len(trackList) > 0:
				trackList = trackList[0]
			audioOutParams = self.player.audio_out_params
			params = self.player.audio_params
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

	def mpvFileEnded(self, event):
		print(event)
		# repeat current song when on repeat 1 mode
		if config.repeatList == '1' and event['event']['reason'] == 0:
			self.playSong(self.currentSong.data())
		# restart queue only when last file ended due to eof
		if not self.getNextSong() and config.repeatList and event['event']['reason'] == 0:
			self.playSongFromQueue(self.playQueueModel.index(0, 0))

	def mpvUrlChanged(self, _name, value):
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
						self.setCurrentSong(self.getNextSong())
						return
				except AttributeError:
					pass
			for n in range(self.playQueueModel.rowCount()):
				print(n)
				checkid = (self.playQueueModel.item(n, 0).data()['id'])
				print('checking against {} '.format(checkid))
				if checkid == id:
					print('this is it!')
					self.setCurrentSong(self.playQueueModel.item(n, 0))
					return
			print('unable to find song in queue :(')

	@pyqtSlot(int)
	def setTrackProgress(self, position):
		try:
			for seekRange in self.player.demuxer_cache_state['seekable-ranges']:
				print('seekable range from {} to {}'.format(seekRange['start'], seekRange['end']))
				if position in range(math.floor(seekRange['start']), math.floor(seekRange['end'])):
					print('seeking to {}'.format(position))
					self.player.command('seek', position, 'absolute+exact')
					return
			print('refusing to seek, file not sufficiently loaded')
		except SystemError:
			pass

	def updateSongDetails(self, _name, value):
		# print('emitting update title')
		value = self.player.media_title
		if value:
			self.updatePlayerUI.emit(value, 'title')
		else:
			self.updatePlayerUI.emit('Not Playing', 'title')
		try:
			artist = self.player.filtered_metadata['Artist']
			self.updatePlayerUI.emit(artist, 'artist')
		except KeyError:
			print('unable to update artist.')
			return
		except TypeError:
			# print('updating artist too early')
			self.updatePlayerUI.emit('No Artist', 'artist')
			return

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

	def removeFromQueue(self, ids):
		print('removing {} from play queue'.format(ids))
		removeRowIds = []
		for n in range(0, self.playQueueModel.rowCount()):
			song = self.playQueueModel.item(n, 0)
			if song and song.data()['id'] in ids:
				removeRowIds.append(n)
		removeRowIds.sort(reverse=True)
		for n in removeRowIds:
			self.playQueueModel.removeRow(n)
		self.syncMpvPlaylist()
