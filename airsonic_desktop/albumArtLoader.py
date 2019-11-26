from PyQt5.QtCore import QRunnable, pyqtSignal, QObject


class albumArtLoaderSignals(QObject):
	albumArtLoaded = pyqtSignal(object, str)


class albumArtLoader(QRunnable):
	def __init__(self, download, albumId):
		super(albumArtLoader, self).__init__()
		self.signals = albumArtLoaderSignals()
		self.download = download
		self.albumId = albumId

	def run(self):
		print('downloading album art {}'.format(self.albumId))
		art = self.download.read(16384)
		while chunk := self.download.read(16384):
			art += chunk
		self.signals.albumArtLoaded.emit(art, self.albumId)
