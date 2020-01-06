import requests
from PyQt5.QtCore import QRunnable, pyqtSignal, QObject
from requests import RequestException

from vapoursonic_pkg.config import config


class albumArtLoaderSignals(QObject):
	albumArtLoaded = pyqtSignal(object, str, str)
	errorHandler = pyqtSignal(object)


class albumArtLoader(QRunnable):
	def __init__(self, albumId, downloadType):
		super(albumArtLoader, self).__init__()
		self.signals = albumArtLoaderSignals()
		self.albumId = albumId
		self.downloadType = downloadType
	
	def run(self):
		# print('downloading album art {}'.format(self.albumId))
		self.url = buildUrl(self.downloadType, self.albumId)
		try:
			r = requests.get(self.url, timeout=10)
		except RequestException as e:
			self.signals.errorHandler.emit(e)
		art = r.content
		self.signals.albumArtLoaded.emit(art, self.albumId, self.downloadType)


def buildUrl(downloadType, albumId):
	if downloadType == 'full':
		return config.fqdn + '/rest/getCoverArt?f=json&v=1.15.0&c=' + \
		           config.appname + '&u=' + config.username + '&s=' + config.salt + \
		           '&t=' + config.token + '&id=' + albumId
	else:
		return config.fqdn + '/rest/getCoverArt?f=json&v=1.15.0&c=' + \
		           config.appname + '&u=' + config.username + '&s=' + config.salt + \
		           '&t=' + config.token + '&id=' + albumId + '&size=256'
