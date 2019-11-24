import math

import mpv
from PyQt5.QtCore import QObject, QThreadPool, QRunnable, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem

import config
import os
import pathlib


class playbackController(QObject):
	getSongHandle = pyqtSignal(object)
	updatePlayerUI = pyqtSignal(object, str)

	def __init__(self, networkWorker):
		super(playbackController, self).__init__()
		self.playQueueModel = QStandardItemModel()
		self.songLoaderThreads = QThreadPool()

		self.player = mpv.MPV(log_handler=print, loglevel='info')
		self.currentPlayer = self.player
		self.player.observe_property('time-pos', self.updateProgressBar)
		self.player.observe_property('media-title', self.updateSongDetails)
		self.player.observe_property('pause', self.updateIdleState)

		self.playQueueModel.setHorizontalHeaderLabels(['Title', 'Artist', 'Album'])
		self.currentSong = None
		self.getSongHandle.connect(networkWorker.getSongHandle)
		networkWorker.returnSongHandle.connect(self.preparePlay)

	# signals

	def addSongs(self, songs):
		# pass in a list of song dicts from the subsonic api, not an album!
		print('adding songs to playqueue')
		print(songs)
		for item in songs:
			standardItems = []
			item = self.improveSong(item)
			for key in ['title', 'artist', 'album']:
				standardItems.append(QStandardItem(item[key]))
			for standardItem in standardItems:
				standardItem.setData(item['id'])
			self.playQueueModel.appendRow(standardItems)

	def improveSong(self, song):  # add expanded song path w/ cache
		song['fullpath'] = os.path.abspath(os.path.join(config.config['cacheLocation'], song['path']))
		pre, ext = os.path.splitext(song['fullpath'])
		try:
			song['fullpath'] = pathlib.Path(song['fullpath']).with_suffix(song['transcoded_suffix'])
		except KeyError:
			pass
		return song

	def playNow(self, allSongs, song):
		# replace the play queue with the album (allSongs), then play song from that album.
		# should assert that song is in allSongs
		self.playQueueModel.clear()
		self.addSongs(allSongs)
		song = self.improveSong(song)
		self.currentSong = song
		self.getSongHandle.emit(song)

	@pyqtSlot(object, object)
	def preparePlay(self, song, download):
		loader = songLoader(song, download)
		loader.signals.readyForPlay.connect(self.play)
		self.songLoaderThreads.start(loader)

	@pyqtSlot(object)
	def play(self, song):
		print('pre-load finished for {}'.format(song['title']))
		if song == self.currentSong:
			self.currentPlayer.play(song['fullpath'])

	def updateProgressBar(self, _name, value):
		progress = value
		total = self.currentSong['duration']
		try:
			percent = progress / total * 100
		except TypeError:  # fires when we are called with a time of 0
			percent = 100  # is this correct?!
		# print("progress: {}, percent: {}". format(value, percent))
		self.updatePlayerUI.emit(math.ceil(percent), 'progress')

	def updateSongDetails(self, _name, value):
		self.updatePlayerUI.emit(value, 'title')

	def updateIdleState(self, _name, value):
		print('player idle state: {}'.format(value))
		self.updatePlayerUI.emit(value, 'idle')

	@pyqtSlot(bool)
	def playPause(self, clicked):
		if self.currentPlayer['pause']:
			self.currentPlayer['pause'] = False
		else:
			self.currentPlayer['pause'] = True


class songLoaderSignals(QObject):
	readyForPlay = pyqtSignal(object)


class songLoader(QRunnable):
	def __init__(self, song, download):
		super().__init__()
		cacheDir = os.path.abspath(config.config['cacheLocation'])
		if not os.path.isdir(cacheDir):
			os.makedirs(cacheDir, exist_ok=True)
		self.signals = songLoaderSignals()
		self.song = song
		self.download = download

	def run(self):
		# TODO: Transcoding might cause us to get a different format, should change the extension somehow
		try:
			fulldir = self.song['fullpath']
			os.stat(fulldir)
			# file already exists, dont download again
			self.download.close()
			self.signals.readyForPlay.emit(self.song)
		except FileNotFoundError:
			self.loadSong()

	def loadSong(self):
		print('loading song {}'.format(self.song['title']))
		fulldir = self.song['fullpath']
		dir = os.path.split(fulldir)
		os.makedirs(dir[0], exist_ok=True)
		writes = 0
		with open(fulldir, 'wb', buffering=16384) as write:
			while chunk := self.download.read(16384):
				write.write(chunk)
				writes += 1
				if writes == 5:
					self.signals.readyForPlay.emit(self.song)
					print('emitted readyForPlay')
		print('closed song {}'.format(self.song['title']))
# check for new file to dl?
