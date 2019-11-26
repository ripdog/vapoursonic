import math
import os
import pathlib

import mpv
from PyQt5.QtCore import QObject, QThreadPool, QRunnable, pyqtSlot, pyqtSignal, QModelIndex
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon

import config


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
		self.player.observe_property('filename', self.filenameChanged)

		self.playQueueModel.setHorizontalHeaderLabels(['Title', 'Artist', 'Album'])
		self.currentSong = None
		# signals
		self.getSongHandle.connect(networkWorker.getSongHandle)
		networkWorker.returnSongHandle.connect(self.preparePlay)

	def changeCurrentSong(self, newsong):
		if self.currentSong:
			try:
				self.currentSong.setIcon(QIcon())
			except RuntimeError:
				pass
		self.currentSong = newsong
		self.currentSong.setIcon(QIcon('icons/baseline-play-arrow.svg'))

	def playNow(self, allSongs, song):
		# replace the play queue with the album (allSongs), then play song from that album.
		# should assert that song is in allSongs
		self.playQueueModel.clear()
		self.changeCurrentSong(self.addSongs(allSongs, song))
		song = self.currentSong.data()
		self.loadIfNecessary(song)

	def improveSong(self, song):  # add expanded song path w/ cache
		song['fullpath'] = os.path.abspath(os.path.join(config.config['cacheLocation'], song['path']))
		pre, ext = os.path.splitext(song['fullpath'])
		try:
			song['fullpath'] = str(pathlib.Path(song['fullpath']).with_suffix("." + song['transcodedSuffix']))
		except KeyError as e:
			pass
		return song

	def addSongs(self, songs, currentSong):
		# pass in a list of song dicts from the subsonic api, not an album!
		print('adding songs to playqueue')
		print(songs)
		for item in songs:
			standardItems = []
			item = self.improveSong(item)
			for key in ['title', 'artist', 'album']:
				standardItems.append(QStandardItem(item[key]))
			for standardItem in standardItems:
				standardItem.setData(item)
			self.playQueueModel.appendRow(standardItems)
			if currentSong and currentSong['id'] == item['id']:
				returnme = standardItems[0]
		self.playQueueModel.setHorizontalHeaderLabels(['Title', 'Artist', 'Album'])
		return returnme

	def loadIfNecessary(self, song):
		try:
			song = song.data()
		except AttributeError:
			pass
		try:
			fulldir = song['fullpath']
			os.stat(fulldir)
			self.play(song)
		except FileNotFoundError:
			self.getSongHandle.emit(song)

	@pyqtSlot(object, object)
	def preparePlay(self, song, download):
		loader = songLoader(song, download)
		loader.signals.readyForPlay.connect(self.play)
		loader.signals.songLoadFinished.connect(self.evaluatePreload)
		self.songLoaderThreads.start(loader)

	@pyqtSlot(object)
	def play(self, song):
		print('pre-load finished for {}'.format(song['title']))
		if song['id'] == self.currentSong.data()['id']:
			self.currentPlayer.playlist_clear()
			self.currentPlayer.play(song['fullpath'])
			self.currentPlayer['pause'] = False
			nextsong = self.getNextSong()
			if nextsong:
				print('preloading next song')
				self.loadIfNecessary(nextsong)
		elif song['id'] == self.getNextSong().data()['id']:
			self.currentPlayer.playlist_append(song['fullpath'])

	@pyqtSlot()
	def playNextSong(self):
		if self.getNextSong():
			song = self.getNextSong()
			self.changeCurrentSong(song)
			self.loadIfNecessary(song)
		else:
			# with no next song, either repeat (TODO) or stop.
			self.currentPlayer.command('stop')

	@pyqtSlot()
	def playPreviousSong(self):
		if self.getPreviousSong():
			song = self.getPreviousSong()
			self.changeCurrentSong(song)
			self.loadIfNecessary(song)
		else:  # if at top of queue, restart song.
			self.currentPlayer.seek(0, 'absolute-percentage')

	@pyqtSlot(QModelIndex)
	def playSongFromQueue(self, index):
		index = index.siblingAtColumn(0)
		song = self.playQueueModel.itemFromIndex(index)
		self.changeCurrentSong(song)
		self.loadIfNecessary(song)

	@pyqtSlot(object)
	def evaluatePreload(self, song):
		if song['id'] == self.currentSong.data()['id']:
			nextsong = self.getNextSong()
			if nextsong:
				print('preloading next song')
				self.loadIfNecessary(nextsong)

	def getPreviousSong(self):
		currentindex = self.playQueueModel.indexFromItem(self.currentSong)
		try:
			return self.playQueueModel.item(currentindex.row() - 1, 0)
		except AttributeError:
			return None

	def getNextSong(self):
		currentindex = self.playQueueModel.indexFromItem(self.currentSong)
		# print('got index for current song: {}'.format(currentindex.row()))
		try:
			return self.playQueueModel.item(currentindex.row() + 1, 0)
		except AttributeError:
			return None

	def updateProgressBar(self, _name, value):
		progress = value
		total = self.currentSong.data()['duration']
		try:
			percent = progress / total * 100
		except TypeError:  # fires when we are called with a time of 0
			percent = 100  # is this correct?!
		# print("progress: {}, percent: {}". format(value, percent))
		self.updatePlayerUI.emit(math.ceil(percent), 'progress')
		if value:
			if math.floor(value) >= self.currentSong.data()['duration']:
				print('song appears done, skipping to next')
				self.playNextSong()

	def filenameChanged(self, _name, value):
		if value:
			print('MPV song changed. mpv path:')
			print(value)
			if value == os.path.basename(self.currentSong.data()['fullpath']):
				print('no need to adjust currentSong')
				return
			try:
				nextpath = self.getNextSong().data()['fullpath']
				print(os.path.basename(nextpath))
				if os.path.basename(nextpath) == value:
					self.changeCurrentSong(self.getNextSong())
					return
			except AttributeError:
				pass
			for n in range(self.playQueueModel.rowCount()):
				print(n)
				path = os.path.basename(self.playQueueModel.item(n, 0).data()['fullpath'])
				print('checking against {} '.format(path))
				if path == value:
					print('this is it!')
					self.changeCurrentSong(self.playQueueModel.item(n, 0))
					return
			print('unable to find song in queue :(')

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
	songLoadFinished = pyqtSignal(object)


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
		print('loading song {}'.format(self.song['title']))
		fulldir = self.song['fullpath']
		dir = os.path.split(fulldir)
		os.makedirs(dir[0], exist_ok=True)
		writes = 0
		with open(fulldir, 'wb', buffering=16384) as write:
			while chunk := self.download.read(16384):
				write.write(chunk)
				writes += 1
				if writes == 8:
					self.signals.readyForPlay.emit(self.song)
					print('emitted readyForPlay')
		print('closed song {}'.format(self.song['title']))
		self.signals.songLoadFinished.emit(self.song)
# check for new file to dl?
