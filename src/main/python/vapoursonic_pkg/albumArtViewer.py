from PyQt5.QtCore import QThreadPool, QPoint, QRect
from PyQt5.QtGui import QImage, QPixmap, QGuiApplication
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel

from vapoursonic_pkg.albumArtLoader import albumArtLoader


class albumArtViewer(QDialog):
	def __init__(self, parent, artId, networkWorker):
		super(albumArtViewer, self).__init__(parent)
		self.artId = artId
		self.albumArtLoaderThreadPool = QThreadPool()

		# UI setup
		self.setSizeGripEnabled(False)
		self.gridLayout = QGridLayout(self)
		self.albumArtLabel = QLabel('Loading...')
		self.gridLayout.addWidget(self.albumArtLabel)
		#Download art
		self.albumArtLoader = albumArtLoader(self.artId, 'full')
		self.albumArtLoader.signals.albumArtLoaded.connect(self.displayAlbumArt)
		self.albumArtLoader.signals.errorHandler.connect(parent.handleError)
		self.albumArtLoaderThreadPool.start(self.albumArtLoader)

	def displayAlbumArt(self, art, _albumId, _type):
		image = QImage()
		image.loadFromData(art)
		self.setFixedSize(image.size())#FIXME: This is too small, make it bigger
		self.albumArtLabel.setPixmap(QPixmap.fromImage(image))
		#center the dialog
		rec = QGuiApplication.screenAt(self.pos()).geometry()
		size = image.size()
		topLeft = QPoint((rec.width() / 2) - (size.width() / 2), (rec.height() / 2) - (size.height() / 2))
		self.setGeometry(QRect(topLeft, size))

