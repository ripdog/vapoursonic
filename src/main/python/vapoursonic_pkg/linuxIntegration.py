import os
import random

from PyQt5.QtCore import QObject, pyqtProperty, Q_CLASSINFO, pyqtSlot
from PyQt5.QtDBus import QDBusConnection, QDBusAbstractAdaptor, QDBusMessage, QDBusObjectPath

# a lot of this was lifted shamelessly from https://github.com/KenjiTakahashi/gayeogi
# Thanks!
from vapoursonic_pkg.config import config


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
class mprisPlayer(QDBusAbstractAdaptor):
	Q_CLASSINFO("D-Bus Interface", "org.mpris.MediaPlayer2.Player")
	
	def __init__(self, parent, playbackController):
		super(mprisPlayer, self).__init__(parent)
		self.setAutoRelaySignals(True)
		self.playbackController = playbackController
		playbackController.updatePlayerUI.connect(self._emitMetadata)
		self.helper = MPRIS2Helper()
	
	@pyqtSlot()
	def Play(self):
		print('play signal sent')
		self.playbackController.playPause()
	
	@pyqtSlot()
	def Pause(self):
		print('pause signal sent')
		self.playbackController.playPause()
	
	@pyqtSlot()
	def Next(self):
		print('Next signal sent')
		self.playbackController.playNextSongExplicitly()
	
	@pyqtSlot()
	def Previous(self):
		print('Next signal sent')
		self.playbackController.playPreviousSong()
	
	@pyqtProperty("QMap<QString, QVariant>")
	def Metadata(self):
		metadata = {}
		currentSong = self.playbackController.currentSongData
		if not currentSong:
			metadata['mpris:trackid'] = QDBusObjectPath(
				'/vapoursonic/notrack'
			)
			return metadata
		metadata = {
			'mpris:trackid': QDBusObjectPath(
				'/vapoursonic/{}'.format(currentSong['id'])
			),
			'xesam:trackNumber': currentSong['track'],
			'xesam:title': currentSong['title'],
			'xesam:album': currentSong['album'],
			'xesam:artist': currentSong['artist'],
			'mpris:length': currentSong['duration'] * 1000000  # convert to microseconds
		}
		return metadata
	
	def _emitMetadata(self, update, updateType):
		if update and updateType == 'newCurrentSong':
			print('emitting new metadata on mpris')
			metadata = {
				'mpris:trackid': QDBusObjectPath(
					'/vapoursonic/{}'.format(update['id'])
				),
				'xesam:trackNumber': update['track'],
				'xesam:title': update['title'],
				'xesam:album': update['album'],
				'xesam:artist': update['artist'],
				'mpris:length': update['duration'] * 1000000  # convert to microseconds
			}
			self.helper.PropertiesChanged(
				'org.mpris.MediaPlayer2.Player', 'Metadata', metadata
			)
		elif updateType == 'idle':
			self.helper.PropertiesChanged("org.mpris.MediaPlayer2.Player",
			                              "PlaybackStatus", self.playbackController.getCurrentPlaybackState())
	
	@pyqtProperty(str)
	def PlaybackStatus(self):
		return self.playbackController.getCurrentPlaybackState()
	
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
	def Shuffle(self, shuffle):
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
	
	@pyqtProperty("qlonglong")
	def Position(self):
		try:
			return self.playbackController.player.time_pos * 1000000
		except:
			return 0.0
	
	@pyqtSlot()
	def PlayPause(self):
		self.playbackController.playPause()


class MPRIS2Helper(object):
	def __init__(self):
		self.signal = QDBusMessage.createSignal(
			"/org/mpris/MediaPlayer2",
			"org.freedesktop.DBus.Properties",
			"PropertiesChanged"
		)
	
	def PropertiesChanged(self, interface, property, values):
		"""Sends PropertiesChanged signal through sessionBus.
		Args:
			interface: interface name
			property: property name
			values: current property value(s)
		"""
		self.signal.setArguments(
			[interface, {property: values}, ['']]
		)
		QDBusConnection.sessionBus().send(self.signal)
