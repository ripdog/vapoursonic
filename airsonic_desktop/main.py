from datetime import timedelta

from PyQt5.QtCore import QThread, pyqtSlot, QModelIndex, pyqtSignal, QObject, QSize
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow

import config
from networkWorker import networkWorker
from playbackController import playbackController
from ui_mainwindow import Ui_AirsonicDesktop


class MainWindowSignals(QObject):
	loadAlbumsOfType = pyqtSignal(str)
	loadAlbumWithId = pyqtSignal(int)


playIcon = QIcon('icons/baseline-play-arrow.svg')
pauseIcon = QIcon('icons/baseline-pause.svg')


class MainWindow(QMainWindow):

	def __init__(self, *args, **kwargs):
		super(MainWindow, self).__init__(*args, **kwargs)
		self.networkThread = QThread()
		self.networkWorker = networkWorker()
		self.networkWorker.moveToThread(self.networkThread)
		self.networkThread.start()
		self.ui = Ui_AirsonicDesktop()
		self.ui.setupUi(self)

		self.populateConnectFields()

		self.ui.stackedWidget.setCurrentIndex(0)

		self.signals = MainWindowSignals()
		self.ui.connectButton.clicked.connect(lambda: self.networkWorker.connectToServer(
			self.ui.domainInput.text(),
			self.ui.usernameInput.text(),
			self.ui.passwordInput.text()
		))
		self.networkWorker.returnAlbums.connect(self.displayLoadedAlbums)
		self.networkWorker.connectResult.connect(self.connectResult)
		self.signals.loadAlbumsOfType.connect(self.networkWorker.getAlbumsOfType)
		self.signals.loadAlbumWithId.connect(self.networkWorker.getAlbumSongs)
		self.networkWorker.returnAlbumSongs.connect(self.displayLoadedSongs)

		self.currentAlbum = None

	def populateConnectFields(self):
		self.ui.domainInput.setText(config.config['domain'])
		self.ui.usernameInput.setText(config.config['username'])
		self.ui.passwordInput.setText(config.config['password'])

	@pyqtSlot(bool)
	def connectResult(self, success):
		print('got connect result: ')
		print(success)
		if success:
			self.ui.stackedWidget.setCurrentIndex(1)
			self.populatePlayerUI()
		else:
			pass

	# should slap an error somewhere lol

	def populatePlayerUI(self):
		# Populate icons
		self.ui.nextTrack.setIcon(QIcon('icons/baseline-skip-next.svg'))
		self.ui.prevTrack.setIcon(QIcon('icons/baseline-skip-previous.svg'))
		self.ui.playPause.setIcon(playIcon)
		self.ui.stop.setIcon(QIcon('icons/baseline-stop.svg'))
		self.ui.search.setClearButtonEnabled(True)
		countIconPixmap = QIcon('icons/audio-spectrum.svg').pixmap(QSize(24, 24))
		lengthIconPixmap = QIcon('icons/baseline-access-time.svg').pixmap(QSize(24, 24))
		yearIconPixmap = QIcon('icons/sharp-date-range.svg').pixmap(QSize(24, 24))
		self.ui.selectedAlbumReleaseYearIcon.setPixmap(yearIconPixmap)
		self.ui.selectedAlbumTrackCountIcon.setPixmap(countIconPixmap)
		self.ui.selectedAlbumTotalLengthIcon.setPixmap(lengthIconPixmap)
		# Populate Left Panel
		self.albumTreeListModel = QStandardItemModel()
		for item in ['Playlists', 'Random', 'Recently Added', 'Artists', 'Albums', 'Folders']:
			standardItem = QStandardItem(item)
			if not item == "Random":
				standardItem.appendRow(QStandardItem('Loading...'))
			self.albumTreeListModel.appendRow(standardItem)
		self.ui.albumTreeList.setModel(self.albumTreeListModel)
		self.ui.albumTreeList.setHeaderHidden(False)
		self.ui.albumTreeList.clicked[QModelIndex].connect(self.albumListClick)
		self.albumTreeListModel.setColumnCount(2)
		self.albumTreeListModel.setHorizontalHeaderLabels(["Album", "Artists"])
		self.ui.albumTreeList.setUniformRowHeights(True)
		self.ui.albumTreeList.setColumnWidth(0, 300)
		self.ui.albumTreeList.setIndentation(0)
		# populate right panel
		self.albumTrackListModel = QStandardItemModel()
		self.ui.albumTrackList.setModel(self.albumTrackListModel)
		self.albumTrackListModel.setHorizontalHeaderLabels(['Track No.', 'Title', 'Artist'])
		self.ui.albumTrackList.setItemsExpandable(False)
		self.ui.albumTrackList.setIndentation(0)
		self.ui.albumTrackList.doubleClicked.connect(self.albumTrackListClick)
		# populate play queue
		self.playbackController = playbackController(self.networkWorker)
		self.ui.playQueueList.setModel(self.playbackController.playQueueModel)
		self.playbackController.updatePlayerUI.connect(self.updatePlayerUI)
		self.ui.playPause.clicked.connect(self.playbackController.playPause)
		self.ui.nextTrack.clicked.connect(self.playbackController.playNextSong)
		self.ui.prevTrack.clicked.connect(self.playbackController.playPreviousSong)

	@pyqtSlot(object, str)
	def updatePlayerUI(self, update, type):
		if type == 'progress':
			self.ui.trackProgressBar.setValue(update)
		if type == 'title':
			self.ui.currentPlayingLabel.setText(update)
		if type == 'idle':
			if update:
				self.ui.playPause.setIcon(playIcon)
			else:
				self.ui.playPause.setIcon(pauseIcon)

	def albumListClick(self, index):
		item = self.albumTreeListModel.itemFromIndex(index)
		text = item.text()
		print('{} clicked, attempting load...'.format(text))
		if text == "Loading...":
			pass
		elif text == "Random":
			self.signals.loadAlbumsOfType.emit("random")
		else:
			if item.data():
				data = int(item.data())
				print('got data {}'.format(data))
				self.signals.loadAlbumWithId.emit(data)

	def albumTrackListClick(self, index):
		item = self.albumTrackListModel.itemFromIndex(index)
		text = item.text()
		print('{} dblclicked in track list, adding to play queue'.format(text))
		self.playbackController.playNow(self.currentAlbum['song'], item.data())

	@pyqtSlot(object, str)
	def displayLoadedAlbums(self, albums, albumType):
		print(albums)
		destination = self.albumTreeListModel.findItems(albumType.capitalize())
		for item in albums['albumList2']['album']:
			print(item)
			standarditem = [QStandardItem(item['name']), QStandardItem(item['artist'])]
			standarditem[0].setData(item['id'])
			# 1 is the 'data role'. I'm not sure what it is, perhaps a way to store
			# multiple types of data in a single item?
			standarditem[1].setData(item['id'])
			destination[0].appendRow(standarditem)

	@pyqtSlot(object)
	def displayLoadedSongs(self, album):
		print(album)
		self.albumTrackListModel.clear()
		albumdeets = album['album']
		albumsongs = albumdeets['song']
		self.ui.selectedAlbumTitle.setText(albumdeets['name'])
		self.ui.selectedAlbumArtist.setText(albumdeets['artist'])
		self.ui.selectedAlbumTrackCount.setText(str(albumdeets['songCount']))
		self.ui.selectedAlbumTotalLength.setText(str(timedelta(seconds=albumdeets['duration'])))
		try:
			self.ui.selectedAlbumReleaseYear.setText(str(albumdeets['year']))
		except KeyError:
			self.ui.selectedAlbumReleaseYear.setText('')
		for song in albumsongs:
			items = []
			if 'track' in song:
				items.append(QStandardItem(str(song['track'])))
			if 'title' in song:
				items.append(QStandardItem(song['title']))
			if 'artist' in song:
				items.append(QStandardItem(song['artist']))
			for item in items:
				item.setData(song)
			self.albumTrackListModel.appendRow(items)
		self.currentAlbum = albumdeets


if __name__ == "__main__":
	app = QApplication([])
	window = MainWindow()
	window.show()
	app.exec_()
