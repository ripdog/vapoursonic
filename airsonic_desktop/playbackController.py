import math
from time import sleep

from PyQt5.QtCore import QObject, QThreadPool, pyqtSlot, pyqtSignal, QModelIndex, QRunnable
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon

import mpv


def my_log(loglevel, component, message):
	print('[{}] {}: {}'.format(loglevel, component, message))


class MpvStream(QObject):
	def __init__(self, url, playbackController):
		super(MpvStream, self).__init__()
		self.id = str(url)[13:-1]
		print('stream object created for id {}'.format(self.id))
		self.playbackController = playbackController
		self.readPos = 0

	def read(self, size):
		while True:
			try:
				cache = self.playbackController.songCache[self.id][1]
			except KeyError:
				print('ERROR: Mpv trying to read unloaded song!')
				sleep(0.1)
				continue
			attempts = 0
			while True:
				if len(cache) - self.readPos >= size:
					# enough data or more than enough is available. Provide data and advance read position.
					ret = cache[self.readPos:self.readPos + size]
					self.readPos += size
					return ret
				elif len(cache) - self.readPos < size:
					# insufficient cache to fufill entire request, just give the rest.
					ret = cache[self.readPos:]
					self.readPos = len(cache)
					return ret
				elif self.playbackController.songCache[self.id][0] == songLoadInProgress:
					sleep(0.1)
				else:
					return b'0'

	def seek(self, offset):
		print('seeking song {} to offset {}'.format(self.id, offset))
		self.readPos = offset
		try:
			if offset > len(self.playbackController.songCache[self.id][1]):
				self.readPos = len(self.playbackController.songCache[self.id][1])
		except IndexError:
			print('seeking on insufficiently loaded file!')
		except KeyError:
			print('seeking on unloaded file!')
		return self.readPos

	def close(self):
		print('closing id {}'.format(self.id))
		self.playbackController.songClose(self.id)


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

		self.player = mpv.MPV(log_handler=my_log, loglevel='info')
		self.player.register_stream_protocol('airsonic', self.createStreamObject)
		self.player['cache-secs'] = 99999999.0
		self.player['demuxer-max-bytes'] = 99999999999
		self.player.observe_property('time-pos', self.updateProgressBar)
		self.player.observe_property('media-title', self.updateSongDetails)
		self.player.observe_property('core-idle', self.updateIdleState)

		self.songCache = {}
		# the cache stores song data. The key is the id of the song, and the value is a list.
		# The first object of the list is a an int denoting the status of the song load. The meanings are above.
		# the second is the bytes object containing the song data.

		self.playQueueModel.setHorizontalHeaderLabels(['Title', 'Artist', 'Album'])
		self.currentSong = None
		# signals

		self.getSongHandle.connect(networkWorker.getSongHandle)
		networkWorker.returnSongHandle.connect(self.loadSongWithHandle)

	def createStreamObject(self, url):
		return MpvStream(url, self)

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

	def nextSongPreloaded(self):
		song = self.getNextSong().data()
		if song:
			return song['id'] in self.songCache.keys()
		else:
			return False

	def songFinishedLoading(self, song):
		self.songCache[song['id']][0] = songLoadFinished
		self.evaluateNextSongForLoad()

	def evaluateNextSongForLoad(self):
		if self.getNextSong() and not self.nextSongPreloaded():
			if not self.getNextSong().data()['id'] in self.songCache.keys():
				self.beginSongLoad(self.getNextSong().data())

	def changeCurrentSong(self, newsong):
		if self.currentSong:
			try:
				self.currentSong.setIcon(QIcon())
			except RuntimeError:
				pass
		self.currentSong = newsong
		if newsong:
			self.currentSong.setIcon(QIcon('icons/baseline-play-arrow.svg'))

	def loadSongWithHandle(self, song, handle):
		if song['id'] in self.songCache and \
				self.songCache[song['id']][0] == songLoadFinished:
			print('ignoring song load request for {}'.format(song['title']))
		print('preparing to load song {}'.format(song['title']))
		self.songCache[song['id']] = [1, b'']
		worker = songLoader(song, handle)
		worker.signals.songLoadFinished.connect(self.songFinishedLoading)
		worker.signals.songChunkReturn.connect(self.songChunkReceive)
		self.songLoaderThreads.start(worker)

	def beginSongLoad(self, song):
		print('evaluating song for load, {} id {}'.format(song['title'], song['id']))
		if song['id'] in self.songCache.keys():
			if self.currentSong.data()['id'] == song['id'] and \
					self.player.path != 'airsonic://{}'.format(self.currentSong.data()['id']):
				print('already loaded, playing now')
				self.playSong(song)
			else:
				print('Already loaded')
				return
		else:
			print('Loading')
			self.getSongHandle.emit(song)

	def songChunkReceive(self, id, chunk):
		if not id in self.songCache:
			self.songCache[id] = [1, b'']
		self.songCache[id][0] = songLoadInProgress
		self.songCache[id][1] += chunk
		#	print('chunk received for {}, size now {}'.format(id, len(self.songCache[id][1])))
		if self.player.path != 'airsonic://{}'.format(self.currentSong.data()['id']):
			self.playSong(self.currentSong)

	def songClose(self, id):
		try:
			del self.songCache[id]
		except KeyError:
			# this should only happen when the play queue has been cleared, so bail
			return
		if id == self.currentSong.data()['id']:
			self.changeCurrentSong(self.getNextSong())
		self.evaluateNextSongForLoad()

	def playNow(self, allSongs, song):
		# replace the play queue with the album (allSongs), then play song from that album.
		# should assert that song is in allSongs
		self.player.command('stop')
		self.clearPlayQueue()
		self.changeCurrentSong(self.addSongs(allSongs, song))
		self.beginSongLoad(song)

	def clearPlayQueue(self):
		self.playQueueModel.clear()
		self.songCache = {}
		self.playQueueModel.setHorizontalHeaderLabels(['Title', 'Artist', 'Album'])

	def addSongs(self, songs, currentSong=None, afterCurrent=False):
		# pass in a list of song dicts from the subsonic api, not an album!
		print('adding {} songs to playqueue'.format(len(songs)))
		# print(songs)
		returnme = None
		if afterCurrent and self.currentSong:
			row = self.playQueueModel.indexFromItem(self.currentSong).row() + 1
		else:
			row = None
		for item in songs:
			standardItems = []
			for key in ['title', 'artist', 'album']:
				standardItems.append(QStandardItem(item[key]))
			for standardItem in standardItems:
				standardItem.setData(item)
			if row:
				self.playQueueModel.insertRow(row, standardItems)
				print('inserting row for {}'.format(item['title']))
			else:
				self.playQueueModel.appendRow(standardItems)
			if currentSong and currentSong['id'] == item['id']:
				returnme = standardItems[0]
		if self.currentSongFullyLoaded():
			self.evaluateNextSongForLoad()
		self.syncMpvPlaylist()
		return returnme

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
				self.player.playlist_append('airsonic://' + song.data()['id'])
				index += 1
			else:
				break

	def playSong(self, song):
		# self.changeCurrentSong(song)
		try:
			song = song.data()
		except AttributeError:
			pass
		url = "airsonic://" + song['id']
		self.player.play(url)
		self.player['pause'] = False
		self.syncMpvPlaylist()

	@pyqtSlot()
	def playNextSongExplicitly(self):
		if self.getNextSong():
			song = self.getNextSong()
			self.changeCurrentSong(song)
			self.beginSongLoad(song.data())
		else:
			# with no next song, either repeat (TODO) or stop.
			self.player.command('stop')

	@pyqtSlot()
	def playPreviousSong(self):
		if self.getPreviousSong():
			song = self.getPreviousSong()
			self.changeCurrentSong(song)
			self.beginSongLoad(song.data())
		else:  # if at top of queue, restart song.
			self.player.seek(0, 'absolute-percentage+exact')

	@pyqtSlot(QModelIndex)
	def playSongFromQueue(self, index):
		index = index.siblingAtColumn(0)
		song = self.playQueueModel.itemFromIndex(index)
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
		value = self.player.time_pos  # Get the value direct from player to ensure not getting a
		# leftover from offPlayer
		duration = self.player.duration

		# print("progress: {}, percent: {}".format(value, percent))
		if value and duration:
			self.updatePlayerUI.emit(math.ceil(total), 'total')
			self.updatePlayerUI.emit(math.ceil(value), 'progress')


	# print('mpv pos ceil\'d: {}, max: {}'.format(math.ceil(value), self.currentSong.data()['duration']))

	@pyqtSlot(int)
	def setTrackProgress(self, position):
		try:
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
	def playPause(self, clicked=False):
		if self.player['pause']:
			self.player['pause'] = False
		else:
			self.player['pause'] = True


class songLoaderSignals(QObject):
	songChunkReturn = pyqtSignal(object, object)
	songLoadFinished = pyqtSignal(object)


class songLoader(QRunnable):
	def __init__(self, song, download):
		super().__init__()
		self.signals = songLoaderSignals()
		self.song = song
		self.download = download

	def run(self):
		print('loading song {}'.format(self.song['title']))
		id = self.song['id']
		while chunk := self.download.read(65536):
			self.signals.songChunkReturn.emit(id, chunk)
		# print('emitted songChunkReturn')
		print('Song load finished for {}'.format(self.song['title']))
		self.signals.songLoadFinished.emit(self.song)
