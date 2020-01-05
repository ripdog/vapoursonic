import requests
from PyQt5.QtCore import QRunnable, pyqtSignal, QObject
from requests import RequestException

from vapoursonic_pkg.config import config


class albumArtLoaderSignals(QObject):
	albumArtLoaded = pyqtSignal(object, str, str)
	errorHandler = pyqtSignal(object)


class albumArtLoader(QRunnable):
	def __init__(self, albumId, type):
		super(albumArtLoader, self).__init__()
		self.signals = albumArtLoaderSignals()
		self.albumId = albumId
		self.type = type

	def run(self):
		print('downloading album art {}'.format(self.albumId))
		self.buildUrl()
		try:
			r = requests.get(self.url, timeout=10)
		except RequestException as e:
			self.signals.errorHandler.emit(e)
		art = r.content
		self.signals.albumArtLoaded.emit(art, self.albumId, self.type)

	def buildUrl(self):
		if self.type == 'full':
			self.url = config.fqdn + '/rest/getCoverArt?f=json&v=1.15.0&c=' + \
					   config.appname + '&u=' + config.username + '&s=' + config.salt + \
					   '&t=' + config.token + '&id=' + self.albumId
		else:
			self.url = config.fqdn + '/rest/getCoverArt?f=json&v=1.15.0&c=' + \
					   config.appname + '&u=' + config.username + '&s=' + config.salt + \
					   '&t=' + config.token + '&id=' + self.albumId + '&size=128'
