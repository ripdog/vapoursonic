from PyQt5.QtCore import QRunnable, pyqtSignal, QObject


class albumArtLoaderSignals(QObject):
	albumArtLoaded = pyqtSignal(object, str, str)


class albumArtLoader(QRunnable):
	def __init__(self, download, albumId, type):
		super(albumArtLoader, self).__init__()
		self.signals = albumArtLoaderSignals()
		self.download = download
		self.albumId = albumId
		self.type = type

	def run(self):
		print('downloading album art {}'.format(self.albumId))
		art = self.download.read(16384)
		while True:
			chunk = self.download.read(16384)
			if not chunk:
				break
			art += chunk
		self.signals.albumArtLoaded.emit(art, self.albumId, self.type)
