import math
import os
from _md5 import md5
from time import perf_counter, sleep

import mpv
from PyQt5.QtCore import QObject, QThreadPool, pyqtSlot, pyqtSignal, QModelIndex
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon

from config import config


def print1(level, prefix, message):
	print('MPV 1 message: {}'.format(message))


def print2(level, prefix, message):
	print('MPV 2 message: {}'.format(message))


class playbackController(QObject):
	updatePlayerUI = pyqtSignal(object, str)

	def __init__(self, networkWorker):
		super(playbackController, self).__init__()
		self.playQueueModel = QStandardItemModel()

		self.songLoaderThreads = QThreadPool()

		self.player1 = mpv.MPV(log_handler=print1, loglevel='info')
		self.player2 = mpv.MPV(log_handler=print2, loglevel='info')
		self.player1.playerNo = 1
		self.player1['cache-secs'] = 99999999.0
		self.player1['demuxer-max-bytes'] = 99999999999
		self.player2.playerNo = 2
		self.player2['cache-secs'] = 99999999.0
		self.player2['demuxer-max-bytes'] = 99999999999
		self.currentPlayer = self.player1
		self.offPlayer = self.player2

		self.playQueueModel.setHorizontalHeaderLabels(['Title', 'Artist', 'Album'])
		self.currentSong = None
		# signals
		self.currentSongFullyLoaded = False
		self.nextSongPreloaded = False

		self.salt = md5(os.urandom(100)).hexdigest()
		self.token = md5((config['password'] + self.salt).encode('utf-8')).hexdigest()

	def changeCurrentSong(self, newsong):
		if self.currentSong:
			try:
				self.currentSong.setIcon(QIcon())
			except RuntimeError:
				pass
		self.currentSong = newsong
		if newsong:
			self.currentSong.setIcon(QIcon('icons/baseline-play-arrow.svg'))

	def playNow(self, allSongs, song):
		# replace the play queue with the album (allSongs), then play song from that album.
		# should assert that song is in allSongs
		self.clearPlayQueue()
		self.changeCurrentSong(self.addSongs(allSongs, song))
		self.playSong(song)

	def clearPlayQueue(self):
		self.playQueueModel.clear()
		self.playQueueModel.setHorizontalHeaderLabels(['Title', 'Artist', 'Album'])

	def connectObservables(self):
		print('attempting to connect observables')
		try:
			self.offPlayer.unobserve_property('time-pos', self.updateProgressBar)
			self.offPlayer.unobserve_property('media-title', self.updateSongDetails)
			self.offPlayer.unobserve_property('pause', self.updateIdleState)
		except ValueError:
			print('no need to unobserve yet')
		self.currentPlayer.observe_property('time-pos', self.updateProgressBar)
		self.currentPlayer.observe_property('media-title', self.updateSongDetails)
		self.currentPlayer.observe_property('pause', self.updateIdleState)

	def addSongs(self, songs, currentSong=None, afterCurrent=False):
		# pass in a list of song dicts from the subsonic api, not an album!
		print('adding songs to playqueue')
		print(songs)
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
		if self.currentSongFullyLoaded and afterCurrent:
			self.preloadNextSong(force=True)  # TODO: Is this safe? Should it happen
		# regardless to ensure the correct song is preloaded?
		return returnme

	def getUrlForSongId(self, id):
		return config['fqdn'] + '/rest/download.view?f=json&v=1.15.0&c=' + \
			   config['appname'] + '&u=' + config['username'] + '&s=' + self.salt + \
			   '&t=' + self.token + '&id=' + id

	def playSong(self, song):
		# self.changeCurrentSong(song)
		try:
			song = song.data()
		except AttributeError:
			pass
		url = self.getUrlForSongId(song['id'])
		self.connectObservables()
		self.currentPlayer.play(url)
		self.currentPlayer['pause'] = False
		self.currentSongFullyLoaded = False
		self.nextSongPreloaded = False

	def preloadNextSong(self, force=False):
		if self.getNextSong() and (not self.nextSongPreloaded or force):
			self.offPlayer['pause'] = True
			self.offPlayer.play(
				self.getUrlForSongId(
					self.getNextSong().data()['id']
				)
			)
			self.nextSongPreloaded = True

	def gaplesslyAdvance(self):
		timeStart = perf_counter()
		print('gaplesslyAdvancing to {}'.format(self.getNextSong().data()['title']))
		self.changeCurrentSong(self.getNextSong())
		self.currentPlayer, self.offPlayer = self.offPlayer, self.currentPlayer
		self.connectObservables()
		print('players swapped')
		self.currentPlayer['pause'] = False
		timeEnd = perf_counter()
		print('this gaplessAdvance took {} seconds'.format(timeEnd - timeStart))
		self.offPlayer.time_pos = 0
		self.offPlayer.command('stop')
		self.currentSongFullyLoaded = False
		self.nextSongPreloaded = False

	@pyqtSlot()
	def playNextSongExplicitly(self):
		if self.getNextSong():
			song = self.getNextSong()
			self.changeCurrentSong(song)
			self.playSong(song)
		else:
			# with no next song, either repeat (TODO) or stop.
			self.currentPlayer.command('stop')

	@pyqtSlot()
	def playPreviousSong(self):
		if self.getPreviousSong():
			song = self.getPreviousSong()
			self.changeCurrentSong(song)
			self.playSong(song)
		else:  # if at top of queue, restart song.
			self.currentPlayer.seek(0, 'absolute-percentage+exact')

	@pyqtSlot(QModelIndex)
	def playSongFromQueue(self, index):
		index = index.siblingAtColumn(0)
		song = self.playQueueModel.itemFromIndex(index)
		self.changeCurrentSong(song)
		self.playSong(song)

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
			return None
		# print('got index for current song: {}'.format(currentindex.row()))
		try:
			return self.playQueueModel.item(currentindex.row() + 1, 0)
		except AttributeError:
			return None

	def updateProgressBar(self, _name, _value):
		try:  # observables might not be getting changed properly. Perhaps add handlers specific to each player which only run when their player is current? Ugh.
			# Hold on, perhaps we could ignore `value` and just grab the value direct from self.currentPlayer?!
			total = self.currentSong.data()['duration']
		except RuntimeError:
			print('updateProgressBar here: currentsong has been deleted.')
			return
		value = self.currentPlayer.time_pos  # Get the value direct from currentPlayer to ensure not getting a
		duration = self.currentPlayer.duration
		# leftover from offPlayer
		# print("progress: {}, percent: {}". format(value, percent))
		if value and duration:
			self.updatePlayerUI.emit(math.ceil(self.currentSong.data()['duration']), 'total')
			self.updatePlayerUI.emit(math.ceil(value), 'progress')
			#
			# print('currentSongFullyLoaded: {}'.format(self.currentSongFullyLoaded))
			if value >= duration / 2 and not self.currentSongFullyLoaded:
				self.currentSongFullyLoaded = True
				if self.getNextSong():
					print('preloading {}'.format(self.getNextSong().data()['title']))
					print('value: {}, duration: {}'.format(value, self.currentPlayer.duration))
					self.preloadNextSong()
			elif duration > 2 and \
					duration - value <= 0.5:
				if self.nextSongPreloaded:
					print('Less than 0.5s remaining')
					print('value: {}, duration: {}'.format(value, duration))
					print('sleeping {} seconds'.format((duration - value) - 0.2))
					sleep((duration - value) - 0.2)
					print('current playback time: {}, duration: {}'.format(self.currentPlayer.time_pos, duration))
					self.gaplesslyAdvance()
				else:  # this should be the end of the queue
					self.changeCurrentSong(None)

	# print('mpv pos ceil\'d: {}, max: {}'.format(math.ceil(value), self.currentSong.data()['duration']))

	@pyqtSlot(int)
	def setTrackProgress(self, position):
		try:
			self.currentPlayer.command('seek', position, 'absolute+exact')
		except SystemError:
			pass

	def updateSongDetails(self, _name, value):
		# print('emitting update title')
		value = self.currentPlayer.media_title
		self.updatePlayerUI.emit(value, 'title')

	def updateIdleState(self, _name, value):
		# print('player idle state: {}'.format(value))
		value = self.currentPlayer.core_idle
		self.updatePlayerUI.emit(value, 'idle')

	@pyqtSlot(bool)
	def playPause(self, clicked=False):
		if self.currentPlayer['pause']:
			self.currentPlayer['pause'] = False
		else:
			self.currentPlayer['pause'] = True
