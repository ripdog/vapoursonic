import os
from PyQt5.QtCore import QObject, pyqtProperty, Q_CLASSINFO, pyqtSlot, QMetaType, pyqtSignal
from PyQt5.QtDBus import QDBusConnection, QDBusAbstractAdaptor, QDBusMessage, QDBusObjectPath, QDBusArgument

# a lot of this was lifted shamelessly from https://github.com/KenjiTakahashi/gayeogi
# Thanks!
from vapoursonic_pkg.config import config
from vapoursonic_pkg.albumArtLoader import buildUrl


class mprisIntegration(QObject):
	def __init__(self, playbackController):
		super(mprisIntegration, self).__init__()
		mprisMain(self, playbackController)
		mprisPlayer(self, playbackController)
		self.connection = QDBusConnection.sessionBus()
		self.connection.registerObject("/org/mpris/MediaPlayer2", self)
		self.serviceName = "org.mpris.MediaPlayer2.vapoursonic.instance{}".format(os.getpid())
		self.connection.registerService(self.serviceName)


class mprisMain(QDBusAbstractAdaptor):
	Q_CLASSINFO("D-Bus Interface", "org.mpris.MediaPlayer2")
	
	def __init__(self, parent, playbackController):
		super(mprisMain, self).__init__(parent)
		self.setAutoRelaySignals(True)
		self.playbackController = playbackController
	
	@pyqtProperty(bool)
	def CanQuit(self):
		return False
	
	@pyqtProperty(bool)
	def CanRaise(self):
		return True
	
	@pyqtProperty(bool)
	def HasTrackList(self):
		# return True TODO
		return False
	
	@pyqtProperty(str)
	def Identity(self):
		return 'vapoursonic'
	
	@pyqtProperty(str)
	def DesktopEntry(self):
		return 'vapoursonic'
	
	@pyqtProperty('QStringList')
	def SupportedUriSchemes(self):
		return ['https']
	
	@pyqtProperty('QStringList')
	def SupportedMimeTypes(self):
		return ['audio/mpeg', 'audio/ogg']
	
	@pyqtProperty('QStringList')
	def SupportedInterfaces(self):
		return ['player']


# noinspection PyArgumentList
def buildMetadataDict(song):
	return {
		'mpris:trackid': QDBusObjectPath(
			'/vapoursonic/{}'.format(song['id'])
		),
		'xesam:trackNumber': song['track'],
		'xesam:title': song['title'],
		'xesam:album': song['album'],
		'xesam:artist': song['artist'],
		'mpris:length': song['duration'] * 1000000,  # convert to microseconds
		'mpris:artUrl': buildUrl('currentlyPlaying',
		                         song['coverArt']) if 'coverArt' in song else ""
	}


class mprisPlayer(QDBusAbstractAdaptor):
	Q_CLASSINFO("D-Bus Interface", "org.mpris.MediaPlayer2.Player")
	
	def __init__(self, parent, playbackController):
		super(mprisPlayer, self).__init__(parent)
		self.setAutoRelaySignals(True)
		self.playbackController = playbackController
		playbackController.updatePlayerUI.connect(self._emitMetadata)
		playbackController.idleUpdate.connect(self._emitIdleUpdate)
		playbackController.seeked.connect(self._emitSeeked)
		playbackController.volumeSet.connect(self._emitVolume)
		self.helper = MPRIS2Helper()
	
	@pyqtSlot()
	def Play(self):
		self.playbackController.playPause()
	
	@pyqtSlot()
	def Pause(self):
		# print('pause signal sent')
		self.playbackController.playPause()
	
	@pyqtSlot()
	def Next(self):
		# print('Next signal sent')
		self.playbackController.playNextSongExplicitly()
	
	@pyqtSlot()
	def Previous(self):
		# print('Next signal sent')
		self.playbackController.playPreviousSong()
	
	@pyqtProperty("QMap<QString, QVariant>")
	def Metadata(self):
		if not self.playbackController.currentSongData:
			metadata = {'mpris:trackid': QDBusObjectPath(
				'/vapoursonic/notrack'
			)}
			return metadata
		return buildMetadataDict(self.playbackController.currentSongData)
	
	def _emitMetadata(self, update, updateType):
		if update and updateType == 'newCurrentSong':
			self.helper.PropertiesChanged(
				'org.mpris.MediaPlayer2.Player', 'Metadata', buildMetadataDict(update)
			)
	
	@pyqtProperty(str)
	def PlaybackStatus(self):
		return self.playbackController.getCurrentPlaybackState()
	
	def _emitIdleUpdate(self, _):
		self.helper.PropertiesChanged("org.mpris.MediaPlayer2.Player",
		                              "PlaybackStatus", self.playbackController.getCurrentPlaybackState())
	
	@pyqtProperty(str)
	def RepeatStatus(self):
		if config.repeatList is 1:
			return 'Track'
		elif config.repeatList:
			return 'Playlist'
		else:
			return 'None'
	
	@pyqtProperty(float)
	def Rate(self):
		return 1.0
	
	@Rate.setter
	def Rate(self, rate):
		pass
	
	@pyqtProperty(bool)
	def Shuffle(self):
		return False
	
	@Shuffle.setter
	def Shuffle(self, _):
		self.playbackController.shufflePlayQueue()
	
	@pyqtProperty(float)
	def MinimumRate(self):
		return 1.0
	
	@pyqtProperty(float)
	def MaximumRate(self):
		return 1.0
	
	@pyqtProperty(bool)
	def CanGoNext(self):
		if self.playbackController.getNextSong() or config.repeatList:
			return True
		else:
			return False
	
	@pyqtProperty(bool)
	def CanGoPrevious(self):
		if self.playbackController.getPreviousSong():
			return True
		else:
			return False
	
	@pyqtProperty(bool)
	def CanPlay(self):
		if self.playbackController.currentSongData:
			return True
		else:
			return False
	
	@pyqtProperty(bool)
	def CanPause(self):
		if self.playbackController.currentSongData and not self.playbackController.player.core_idle:
			return True
		else:
			return False
	
	@pyqtSlot("qlonglong")
	def Seek(self, offset):
		# print('seeking to {}'.format(offset))
		newtime = self.playbackController.player.time_pos + (offset / 1000000)
		self.playbackController.setTrackProgress(newtime)
	
	Seeked = pyqtSignal('qlonglong')
	
	def _emitSeeked(self, position):
		self.Seeked.emit(position * 1000000)
	
	@pyqtSlot(QDBusObjectPath, "qlonglong")
	def SetPosition(self, trackId, position):
		# print('seeking track id {} position to {}'.format(trackId.path(), position / 1000000))
		if trackId.path() == '/vapoursonic/{}'.format(self.playbackController.currentSongData['id']):
			self.playbackController.setTrackProgress(position / 1000000)
	
	@pyqtProperty(bool)
	def CanSeek(self):
		return True
	
	@pyqtProperty(bool)
	def CanControl(self):
		return True
	
	@pyqtProperty(float)
	def Volume(self):
		try:
			return self.playbackController.player.volume / 100
		except:
			pass
	
	@Volume.setter
	def Volume(self, volume):
		self.playbackController.setVolume(int(volume * 100))
	
	def _emitVolume(self, volume):
		self.helper.PropertiesChanged("org.mpris.MediaPlayer2.Player",
		                              "Volume", volume / 100)
	
	@pyqtProperty("qlonglong")
	def Position(self):
		try:
			return self.playbackController.player.time_pos * 1000000
		except:
			return 0.0
	
	@pyqtSlot()
	def PlayPause(self):
		self.playbackController.playPause()


# noinspection PyCallByClass
class MPRIS2Helper(object):
	def __init__(self):
		self.signal = QDBusMessage.createSignal(
			"/org/mpris/MediaPlayer2",
			"org.freedesktop.DBus.Properties",
			"PropertiesChanged"
		)
	
	def PropertiesChanged(self, interface, prop, values):
		"""Sends PropertiesChanged signal through sessionBus.
		Args:
			interface: interface name
			prop: property name
			values: current property value(s)
		"""
		emptyStringListArg = QDBusArgument()
		emptyStringListArg.add([""], QMetaType.QStringList)
		self.signal.setArguments([interface, {prop: values}, emptyStringListArg])
		QDBusConnection.sessionBus().send(self.signal)
