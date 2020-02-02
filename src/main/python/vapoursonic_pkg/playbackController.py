import math
import os
import random
import re
import sys
import threading
from datetime import timedelta

from PyQt5.QtCore import QObject, QThreadPool, pyqtSlot, pyqtSignal, QModelIndex, QTimer
from PyQt5.QtGui import QIcon
from fbs_runtime.application_context.PyQt5 import ApplicationContext

try:
	path = os.path.dirname(ApplicationContext().get_resource('mpv-1.dll'))
	os.environ['PATH'] = path + os.pathsep + os.environ['PATH']
except FileNotFoundError:
	if sys.platform == 'win32':
		print('WARNING: Unable to find mpv dll.')

import mpv
from vapoursonic_pkg.config import config


def my_log(loglevel, component, message):
	print('[{}] {}: {}'.format(loglevel, component, message))


# noinspection PyArgumentList
def buildUrlForSong(song):
	if config.streamTypeDownload:
		baseurl = '/rest/download?f=json&v=1.15.0&c='
	else:
		baseurl = '/rest/stream?f=json&v=1.15.0&c='
	return config.fqdn + baseurl + \
		   config.appname + '&u=' + config.username + '&s=' + config.salt + \
		   '&t=' + config.token + '&id=' + song['id']


class playbackController(QObject):
	updatePlayerUI = pyqtSignal(object, str)
	trackProgressUpdate = pyqtSignal(int, int)
	idleUpdate = pyqtSignal(bool)
	seeked = pyqtSignal(int)
	volumeSet = pyqtSignal(int)
	currentPlayingModelChanged = pyqtSignal(object)

	_handleMpvEvent = pyqtSignal(object)

	def __init__(self, defaultModel):
		super(playbackController, self).__init__()
		self.playQueueModel = defaultModel
		self.songLoaderThreads = QThreadPool()

		self.player = mpv.MPV(log_handler=my_log, loglevel='warn')
		self.player['prefetch-playlist'] = True
		self.player['gapless-audio'] = True
		self.player['force-seekable'] = True
		self.player['demuxer-max-back-bytes'] = 999999999
		self.player['cache-secs'] = 99999999.0
		self.player['demuxer-max-bytes'] = 99999999999
		self._handleMpvEvent.connect(self._mpvEventHandler)
		self.player.observe_property('core-idle', self.updateIdleState)
		self.player.register_event_callback(self.mpvEventHandler)

		self.currentSong = None
		self.currentSongData = None

		# create timer for 1-per-second playback status update
		self.secondTimer = QTimer()
		self.secondTimer.timeout.connect(self.everySecond)
		self.secondTimer.start(1000)

	def everySecond(self):
		if self.currentSongData and not self.player.core_idle:
			self.updatePlaybackProgressText()
			self.updateAudioStatLine()
			self.updateProgressBar()

	def updatePlaybackProgressText(self):
		if self.currentSongData and self.player.time_pos:
			current = str(timedelta(seconds=int(self.player.time_pos)))
			total = str(timedelta(seconds=int(self.currentSongData['duration'])))
			self.updatePlayerUI.emit(current + "/" + total, 'progressText')
		else:
			self.updatePlayerUI.emit('00:00/00:00', 'progressText')

	def getCurrentPlaybackState(self):
		if self.currentSongData and self.currentSongData['type'] == 'song':
			# song is loaded
			if self.player.core_idle:
				return 'Paused'
			else:
				return 'Playing'
		else:
			return 'Stopped'

	def setCurrentSong(self, newsong):
		if newsong is None:
			print('setting current song to None. Caller: {}'.format(sys._getframe().f_back.f_code.co_name))
		if self.currentSong:
			try:
				if not threading.current_thread() is threading.main_thread():
					self.setCurrentSongIcon.emit(self.currentSong)
				else:
					self.currentSong.setIcon(QIcon())
			except RuntimeError:
				pass
		self.currentSong = newsong
		if newsong:
			self.currentSongData = newsong.data()
			self.updatePlaybackProgressText()
			self.currentSong.setIcon(config.icons['baseline-play-arrow.svg'])
			self.updatePlayerUI.emit(self.playQueueModel.indexFromItem(self.currentSong), 'scrollTo')

	def stop(self):
		self.setCurrentSong(None)
		self.player.command('stop')

	def shufflePlayQueue(self, model):
		items = []
		if model == self.playQueueModel:
			currsong = self.currentSongData
			for item in range(model.rowCount()):
				item = model.item(item, 0).data()
				if not item['id'] == self.currentSongData['id']:
					items.append(item)
			random.shuffle(items)
			items.insert(0, currsong)
		else:
			for item in range(model.rowCount()):
				items.append(model.item(item, 0).data())
			random.shuffle(items)

		self.clearPlayQueue(model)
		self.addSongs(items, model)
		if model == self.playQueueModel:
			self.setCurrentSong(self.playQueueModel.item(0, 0))
			self.syncMpvPlaylist()

	def clearPlayQueue(self, model):
		model.clear()
		if model == self.playQueueModel:
			self.syncMpvPlaylist()
			self.playQueueModel.refreshHeaderLabels()

	def setPlayQueue(self, model):
		self.playQueueModel = model
		self.currentPlayingModelChanged.emit(model)

	def addSongs(self, songs, model, playThisSongNow=None, afterCurrent=False):
		"""
		This function adds songs to the play queue, optionally playing them.
		Set `songs` to a list of song dicts.
		Set `model` to the PlayQueueModel object you want to add to.
		To play a song after adding, set 'playThisSongNow' to a song dict.
		Set afterCurrent to True if you want the songs appended after the currently playing song.
		"""
		print('adding {} songs to playqueue'.format(len(songs)))
		currentSongStandardObject = None
		if playThisSongNow:
			self.setPlayQueue(model)
			self.clearPlayQueue(model)
		if afterCurrent and self.currentSong:
			if model == self.playQueueModel:
				insertAfterRow = self.playQueueModel.indexFromItem(self.currentSong).row() + 1
			else:
				insertAfterRow = 0  # Add to top of non-active playlists
		else:
			insertAfterRow = None
		currentSongStandardObject = model.addSongs(songs, playThisSongNow, insertAfterRow)
		if currentSongStandardObject:
			self.setCurrentSong(currentSongStandardObject)
			self.playSong(currentSongStandardObject.data())
		else:
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
				self.player.playlist_append(buildUrlForSong(song.data()))
				index += 1
			else:
				break

	def playSong(self, song):
		url = buildUrlForSong(song)
		# print('playing {}'.format(url))
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

	@pyqtSlot()
	def playPreviousSong(self):
		if not self.currentSong:
			return
		song = self.getPreviousSong()
		if song:
			self.setCurrentSong(song)
			self.playSong(song.data())
		else:
			self.player.seek(0, 'absolute')

	@pyqtSlot(int)
	def setVolume(self, value):
		self.player.volume = value
		self.volumeSet.emit(value)
		config.volume = value

	@pyqtSlot(QModelIndex)
	def playSongFromQueue(self, index, model=None):
		if not model:
			model = self.playQueueModel
		elif model is not self.playQueueModel:
			self.setPlayQueue(model)
		index = index.siblingAtColumn(0)
		song = self.playQueueModel.itemFromIndex(index)
		print('playing {} from queue click'.format(song.data()['title']))
		self.setCurrentSong(song)
		self.playSong(song.data())

	def getPreviousSong(self):
		try:
			currentindex = self.playQueueModel.indexFromItem(self.currentSong)
		except RuntimeError:
			print('Unable to get index for current song')
			return None
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

	def updateProgressBar(self):
		try:
			total = self.currentSongData['duration']
		except RuntimeError:
			print('updateProgressBar here: currentsong has been deleted.')
			return
		except AttributeError:
			print('updateProgressBar here: no currentsong!')
			return
		duration = self.player.duration
		value = self.player.time_pos
		if value and duration:
			self.trackProgressUpdate.emit(math.ceil(value), math.ceil(total))

	def mpvEventHandler(self, event):
		if event['event_id'] in [mpv.MpvEventID.FILE_LOADED, mpv.MpvEventID.END_FILE, mpv.MpvEventID.SEEK]:
			self._handleMpvEvent.emit(event)

	# signal is used here to move execution back to the main thread.

	@pyqtSlot(object)
	def _mpvEventHandler(self, event):
		if event['event_id'] == mpv.MpvEventID.FILE_LOADED:
			self.updateAudioStatLine()
			self.updateProgressBar()
			if self.player.path:
				# print('song loaded, path {}'.format(self.player.path))

				songId = re.search(r'&id=(?P<songId>\d+)$', self.player.path).group('songId')
				# print('found songId {}'.format(songId))
				self.setCurrentSongFromId(songId)
				if self.currentSongData:
					print('Playing song: {}, album {}, artist {}, duration {}, id {}'.format(
						self.currentSongData['title'], self.currentSongData['album'], self.currentSongData['artist'],
						timedelta(seconds=self.currentSongData['duration']), self.currentSongData['id']
					))
				self.updatePlayerUI.emit(self.currentSongData, 'newCurrentSong')
			self.updatePlaybackProgressText()
		elif event['event_id'] == mpv.MpvEventID.END_FILE:
			self.mpvFileEnded(event)
		elif event['event_id'] == mpv.MpvEventID.SEEK:
			print(event)
			self.seeked.emit(self.player.time_pos)

	def updateAudioStatLine(self):
		audioOutParams = {}
		trackList = {}
		try:
			trackList = self.player.track_list
			if len(trackList) > 0:
				trackList = trackList[0]
			audioOutParams = self.player.audio_out_params
			params = self.player.audio_params
		except [AttributeError, IndexError]:
			params = None
		ret = ""
		if self.player.audio_codec_name:
			ret += self.player.audio_codec_name + " | "
		if trackList and 'demux-bitrate' in trackList:
			ret += str(int(trackList['demux-bitrate'] / 1000)) + 'kbps | '
		elif self.player.audio_bitrate:
			ret += '~' + str(int(self.player.audio_bitrate / 1000)) + 'kbps | '
		if trackList and 'demux-samplerate' in trackList:
			ret += str(trackList['demux-samplerate']) + 'hz -> '

		if audioOutParams and 'samplerate' in audioOutParams:
			ret += str(audioOutParams['samplerate']) + 'hz | '
		if params and 'hr-channels' in params:
			ret += str(params['hr-channels']) + ' | '
		self.updatePlayerUI.emit(ret, 'statusBar')

	def mpvFileEnded(self, event):
		# print(event)
		# repeat current song when on repeat 1 mode
		if config.repeatList == '1' and event['event']['reason'] == 0:
			self.playSong(self.currentSongData)
		# restart queue only when last file ended due to eof
		elif not self.getNextSong() and config.repeatList and event['event']['reason'] == 0:
			self.playSongFromQueue(self.playQueueModel.index(0, 0))
		# otherwise we're done, so clear the title/artist indicators
		else:
			self.updatePlayerUI.emit('Not Playing', 'title')
			self.updatePlayerUI.emit('No Artist', 'artist')
			self.updatePlayerUI.emit(0, 'progress')
			self.updatePlayerUI.emit(100, 'total')

	def setCurrentSongFromId(self, songId):
		songId = int(songId)
		if self.currentSongData:
			if songId == int(self.currentSongData['id']):
				# print('no need to adjust currentSong')
				return
			try:
				nextid = int(self.getNextSong().data()['id'])
				if songId == nextid:
					self.setCurrentSong(self.getNextSong())
					return
				previd = int(self.getPreviousSong().data()['id'])
				if songId == previd:
					self.setCurrentSong(self.getPreviousSong())
					return
			except AttributeError:
				pass
		# print('searching for id {}'.format(songId))
		for n in range(self.playQueueModel.rowCount()):
			checkid = int(self.playQueueModel.item(n, 0).data()['id'])
			# print('checking against {} '.format(checkid))
			if checkid == songId:
				# print('this is it!')
				self.setCurrentSong(self.playQueueModel.item(n, 0))
				return
		print('WARNING: unable to find song in queue :(')

	@pyqtSlot(int)
	def setTrackProgress(self, position):
		if position < 0:
			position = 0
		elif position > self.currentSongData['duration']:
			position = self.currentSongData['duration'] - 1
		try:
			for seekRange in self.player.demuxer_cache_state['seekable-ranges']:
				print('seekable range from {} to {}'.format(seekRange['start'], seekRange['end']))
				if math.floor(position) in range(math.floor(seekRange['start']), math.floor(seekRange['end'])):
					print('seeking to {}'.format(position))
					self.player.command('seek', position, 'absolute+exact')
					return
			print('refusing to seek, file not sufficiently loaded')
		except SystemError:
			pass

	def updateIdleState(self, _name, value):
		self.idleUpdate.emit(value)

	@pyqtSlot(bool)
	@pyqtSlot()
	def playPause(self):
		if self.player['pause']:
			self.player['pause'] = False
		else:
			self.player['pause'] = True

	@pyqtSlot(str)
	def playbackControl(self, playbackChangeType):
		if playbackChangeType == 'playPause':
			self.playPause()
		elif playbackChangeType == "nextSong":
			self.playNextSongExplicitly()
		elif playbackChangeType == "prevSong":
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
