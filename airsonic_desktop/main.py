from datetime import timedelta

import keyboard
from PyQt5 import QtGui
from PyQt5.QtCore import QThread, pyqtSlot, QModelIndex, pyqtSignal, QObject, QSize, QThreadPool, \
	Qt, QItemSelectionModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QStyle, QAbstractItemView

try:
	from PyQt5.QtWinExtras import QWinTaskbarProgress, QWinTaskbarButton, QWinThumbnailToolBar, QWinThumbnailToolButton
except ImportError:
	pass
from config import config
from albumArtLoader import albumArtLoader
from networkWorker import networkWorker
from playbackController import playbackController
from ui_mainwindow import Ui_AirsonicDesktop


class MainWindowSignals(QObject):
	loadAlbumsOfType = pyqtSignal(str)
	loadAlbumWithId = pyqtSignal(int)
	loadAlbumArtWithId = pyqtSignal(str)
	playbackControl = pyqtSignal(str)
	getPlaylists = pyqtSignal()
	loadPlaylistSongs = pyqtSignal(str)

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
		self.signals.loadAlbumArtWithId.connect(self.networkWorker.getAlbumArtWithId)
		self.networkWorker.returnAlbumArtHandle.connect(self.startAlbumArtLoad)
		self.signals.getPlaylists.connect(self.networkWorker.getPlaylists)
		self.networkWorker.returnPlaylists.connect(self.receivePlaylists)
		self.signals.loadPlaylistSongs.connect(self.networkWorker.getPlaylistSongs)
		self.networkWorker.returnPlaylistSongs.connect(self.displayLoadedSongs)

		self.currentAlbum = None
		self.albumArtLoaderThreads = QThreadPool()
		self.albumListState = 'home'

	# options are 'home', 'albums', 'artists', 'recentlyAdded', 'recentlyPlayed', 'random', 'search', maybe folders?

	def populateConnectFields(self):
		self.ui.domainInput.setText(config.domain)
		self.ui.usernameInput.setText(config.username)
		self.ui.passwordInput.setText(config.password)

	@pyqtSlot(bool)
	def connectResult(self, success):
		# print('got connect result: ')
		# print(success)
		if success:
			config.domain = self.ui.domainInput.text()
			config.username = self.ui.usernameInput.text()
			config.password = self.ui.passwordInput.text()
			self.ui.stackedWidget.setCurrentIndex(1)
			self.populatePlayerUI()
		else:
			pass

	# should slap an error somewhere lol

	def populateIcons(self):
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
		self.ui.albumListViewPreviousPage.setIcon(QIcon('icons/baseline-navigate-before.svg'))
		self.ui.albumListViewPreviousPage.setText('')
		self.ui.albumListViewNextPage.setIcon(QIcon('icons/baseline-navigate-next.svg'))
		self.ui.albumListViewNextPage.setText('')
		self.ui.albumListViewRefresh.setIcon(QIcon('icons/baseline-refresh.svg'))
		self.ui.albumListViewRefresh.setText('')
		self.ui.backHomeButton.setIcon(QIcon('icons/baseline-arrow-back.svg'))
		self.ui.backHomeButton.setStyleSheet('QPushButton { text-align: left; }')
		self.ui.shufflePlayqueueButton.setIcon(QIcon('icons/baseline-shuffle.svg'))
		followPlayedTrackIcon = QIcon()
		# followPlayedTrackIcon.addFile('icons/baseline-location-disabled.svg', mode=QIcon.Active)
		# followPlayedTrackIcon.addFile('icons/baseline-my-location.svg', mode=QIcon.Normal)
		self.ui.toggleFollowPlayedTrackButton.setIcon(QIcon('icons/baseline-my-location.svg'))

	def populateLeftPanel(self):
		# Populate Left Panel
		self.albumTreeListModel = QStandardItemModel()
		self.ui.backHomeButtonLayout.close()

		self.ui.albumTreeList.setModel(self.albumTreeListModel)
		self.ui.albumTreeList.setHeaderHidden(False)
		self.ui.albumTreeList.clicked[QModelIndex].connect(self.albumListClick)
		self.ui.albumTreeList.setAlternatingRowColors(True)
		self.albumTreeListModel.setColumnCount(2)

		self.ui.albumTreeList.setUniformRowHeights(True)
		self.ui.albumTreeList.setColumnWidth(0, 300)
		self.ui.albumTreeList.setIndentation(0)
		self.ui.backHomeButton.clicked.connect(self.backHome)
		self.ui.albumListViewRefresh.clicked.connect(self.refreshAlbumListView)
		self.backHome()

	def populateRightPanel(self):
		# populate right panel
		self.albumTrackListModel = QStandardItemModel()
		self.albumTrackListModel.setHorizontalHeaderLabels(['Track No.', 'Title', 'Artist'])
		self.ui.albumTrackList.setModel(self.albumTrackListModel)

		self.ui.albumTrackList.setAlternatingRowColors(True)
		self.ui.albumTrackList.setItemsExpandable(False)
		self.ui.albumTrackList.setIndentation(0)
		self.ui.albumTrackList.doubleClicked.connect(self.albumTrackListDoubleClick)
		self.ui.albumTrackList.setContextMenuPolicy(Qt.CustomContextMenu)
		self.ui.albumTrackList.customContextMenuRequested.connect(self.openAlbumTrackListMenu)

	def populatePlayQueue(self):
		# populate play queue
		self.playbackController = playbackController(self.networkWorker)
		self.ui.playQueueList.setModel(self.playbackController.playQueueModel)
		self.ui.playQueueList.doubleClicked.connect(self.playbackController.playSongFromQueue)
		self.playbackController.updatePlayerUI.connect(self.updatePlayerUI)
		self.ui.playPause.clicked.connect(self.playbackController.playPause)
		self.ui.playQueueList.setAlternatingRowColors(True)
		self.ui.nextTrack.clicked.connect(self.playbackController.playNextSongExplicitly)
		self.ui.prevTrack.clicked.connect(self.playbackController.playPreviousSong)
		self.ui.stop.clicked.connect(self.playbackController.stop)
		self.signals.playbackControl.connect(self.playbackController.playbackControl)
		self.ui.trackProgressBar.sliderMoved.connect(self.playbackController.setTrackProgress)
		self.ui.trackProgressBar.setTracking(False)
		self.ui.toggleFollowPlayedTrackButton.setChecked(True)
		self.followPlayedTrack = True
		self.ui.toggleFollowPlayedTrackButton.clicked.connect(self.updateFollowPlayedTrack)
		self.ui.shufflePlayqueueButton.clicked.connect(self.playbackController.shufflePlayQueue)

	def populateThumbnailToolbar(self):
		self.thumbnailToolBar = QWinThumbnailToolBar(self)
		self.thumbnailToolBar.setWindow(self.windowHandle())

		self.playToolbarButton = QWinThumbnailToolButton(self.thumbnailToolBar)
		self.playToolbarButton.setEnabled(True)
		self.playToolbarButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
		self.playToolbarButton.clicked.connect(self.playbackController.playPause)

		self.prevToolbarButton = QWinThumbnailToolButton(self.thumbnailToolBar)
		self.prevToolbarButton.setEnabled(True)
		self.prevToolbarButton.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))
		self.prevToolbarButton.clicked.connect(self.playbackController.playPreviousSong)

		self.nextToolbarButton = QWinThumbnailToolButton(self.thumbnailToolBar)
		self.nextToolbarButton.setEnabled(True)
		self.nextToolbarButton.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipForward))
		self.nextToolbarButton.clicked.connect(self.playbackController.playNextSongExplicitly)

		self.thumbnailToolBar.addButton(self.prevToolbarButton)
		self.thumbnailToolBar.addButton(self.playToolbarButton)
		self.thumbnailToolBar.addButton(self.nextToolbarButton)

	def bindMediaKeys(self):  # it's borked, capn
		self.keyHook = keyboard.hook_key('play/pause media', self.playPause)
		print(keyboard._hooks)

	def cachePlaylists(self):
		self.signals.getPlaylists.emit()

	def populatePlayerUI(self):
		self.populateIcons()

		self.populateLeftPanel()

		self.populateRightPanel()

		self.populatePlayQueue()

		self.populateThumbnailToolbar()

		self.bindMediaKeys()

		self.cachePlaylists()

		# keybinding the media keys
		# keybinder.init()
		# keybinder.register_hotkey(self.winId(), QKeySequence("Media Play"), self.playbackController.playPause)
		if QWinTaskbarProgress:
			self.taskbarButton = QWinTaskbarButton(self)
			self.taskbarButton.setWindow(self.windowHandle())
			self.taskbarProgress = self.taskbarButton.progress()
		else:
			self.taskbarProgress = None

	@pyqtSlot(object, str)
	def updatePlayerUI(self, update, type):
		if type == 'total':
			self.ui.trackProgressBar.setRange(0, update)
			if self.taskbarProgress:
				self.taskbarProgress.setMaximum(update)
		if type == 'progress':
			self.ui.trackProgressBar.setValue(update)
			if self.taskbarProgress:
				self.taskbarProgress.setValue(update)
		if type == 'title':
			self.ui.currentPlayingLabel.setText(update)
		elif type == 'scrollTo':
			if self.followPlayedTrack:
				self.ui.playQueueList.scrollTo(update, QAbstractItemView.PositionAtTop)
				self.ui.playQueueList.selectionModel().select(update, QItemSelectionModel.ClearAndSelect)
		if type == 'idle':
			if update:
				self.ui.playPause.setIcon(playIcon)
				if self.taskbarProgress:
					self.taskbarProgress.setPaused(True)
					self.playToolbarButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
			else:
				self.ui.playPause.setIcon(pauseIcon)
				if self.taskbarProgress:
					self.taskbarProgress.setPaused(False)
					self.taskbarProgress.setVisible(True)
					self.playToolbarButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

	def updateFollowPlayedTrack(self):
		if self.followPlayedTrack:
			self.followPlayedTrack = False
		# self.ui.toggleFollowPlayedTrackButton.setChecked(False)
		else:
			self.followPlayedTrack = True
		# self.ui.toggleFollowPlayedTrackButton.setChecked(True)

	def playPause(self):
		print('playPause hotkey hit')
		self.signals.playbackControl.emit('playPause')

	def albumListClick(self, index):
		item = self.albumTreeListModel.itemFromIndex(index)
		text = item.text()
		print('{} clicked, attempting load...'.format(text))
		if self.albumListState == 'home':
			self.loadDataforAlbumListView(text)
		elif self.albumListState == 'playlists':
			self.loadPlaylistSongs(item.data())
		else:
			if item.data():
				data = int(item.data())
				# print('got data {}'.format(data))
				self.signals.loadAlbumWithId.emit(data)

	def loadPlaylistSongs(self, id):
		self.signals.loadPlaylistSongs.emit(id)

	def receivePlaylists(self, playlists):
		self.playlistCache = []
		print(playlists)
		if 'status' in playlists.keys() and playlists['status'] == 'ok':
			self.playlistCache = playlists['playlists']['playlist']
			if self.albumListState == 'playlists':
				self.albumTreeListModel.setHorizontalHeaderLabels(["Playlist", 'Song Count'])
				self.ui.albumTreeList.setHeaderHidden(False)
				for playlist in playlists['playlists']['playlist']:
					items = []
					item = QStandardItem(playlist['name'])
					item.setData(playlist['id'])
					items.append(item)
					item = QStandardItem(str(playlist['songCount']))
					item.setData(playlist['id'])
					items.append(item)
					self.albumTreeListModel.appendRow(items)

	def loadDataforAlbumListView(self, type):
		type = type.lower()
		self.changeAlbumListState(type)

		if type == "random":
			self.signals.loadAlbumsOfType.emit("random")
		elif type == "recently added":
			self.signals.loadAlbumsOfType.emit("recentlyAdded")
		elif type == "recently played":
			self.signals.loadAlbumsOfType.emit('recentlyPlayed')
		elif type == 'albums':
			self.signals.loadAlbumsOfType.emit('albums')
		elif type == 'playlists':
			self.signals.getPlaylists.emit()

	def albumTrackListDoubleClick(self, index):
		item = self.albumTrackListModel.itemFromIndex(index)
		text = item.text()
		print('{} dblclicked in track list, adding to play queue'.format(text))
		self.playbackController.playNow(self.currentAlbum['song'], item.data())

	def changeAlbumListState(self, state):
		self.albumListState = state
		self.albumTreeListModel.clear()
		if state != 'home':
			self.ui.backHomeButtonLayout.setHidden(False)
		else:
			self.ui.backHomeButtonLayout.setHidden(True)

	@pyqtSlot()
	def backHome(self):
		self.changeAlbumListState('home')
		self.albumTreeListModel.setColumnCount(1)
		self.ui.albumTreeList.setHeaderHidden(True)
		for item in ['Playlists', 'Random', 'Recently Added', 'Recently Played', 'Artists', 'Albums', 'Folders']:
			standardItem = QStandardItem(item)
			self.albumTreeListModel.appendRow(standardItem)

	@pyqtSlot(object, str)
	def displayLoadedAlbums(self, albums, albumType):
		# print(albums)
		self.albumTreeListModel.setHorizontalHeaderLabels(["Album", "Artists"])
		self.ui.albumTreeList.setHeaderHidden(False)
		for item in albums['albumList2']['album']:
			# print(item)
			standarditem = [QStandardItem(item['name']), QStandardItem(item['artist'])]
			standarditem[0].setData(item['id'])
			# 1 is the 'data role'. I'm not sure what it is, perhaps a way to store
			# multiple types of data in a single item?
			standarditem[1].setData(item['id'])
			self.albumTreeListModel.appendRow(standarditem)
		self.ui.albumTreeList.setColumnWidth(0, 250)

	def playlistFromCacheById(self, id):
		for item in self.playlistCache:
			if item['id'] == id:
				return item
		return None

	@pyqtSlot(object)
	def displayLoadedSongs(self, album):
		songs = []
		if 'album' in album:
			albumdeets = album['album']
			songs = albumdeets['song']
		elif 'playlist' in album:
			print(album)
			songs = album['playlist']['entry']
			albumdeets = {}
			albumdeets['name'] = album['playlist']['name']
			albumdeets['artist'] = ''
			albumdeets['songCount'] = len(songs)
			albumdeets['duration'] = self.playlistFromCacheById(album['playlist']['id'])['duration']
			albumdeets['coverArt'] = self.playlistFromCacheById(album['playlist']['id'])['coverArt']
			albumdeets['song'] = songs

		self.albumTrackListModel.clear()
		self.albumTrackListModel.setHorizontalHeaderLabels(['Track No.', 'Title', 'Artist'])

		try:
			self.signals.loadAlbumArtWithId.emit(albumdeets['coverArt'])
		except KeyError:
			print('no cover art :(')
			self.ui.selectedAlbumArt.setText("No Art")
			pass
		self.ui.selectedAlbumTitle.setText(albumdeets['name'])
		self.ui.selectedAlbumArtist.setText(albumdeets['artist'])
		self.ui.selectedAlbumTrackCount.setText(str(albumdeets['songCount']))
		self.ui.selectedAlbumTotalLength.setText(str(timedelta(seconds=albumdeets['duration'])))
		try:
			self.ui.selectedAlbumReleaseYear.setText(str(albumdeets['year']))
		except KeyError:
			self.ui.selectedAlbumReleaseYear.setText('')
		for song in songs:
			items = []
			if 'track' in song:
				items.append(QStandardItem(str(song['track'])))
			else:
				items.append(QStandardItem("-"))
			if 'title' in song:
				items.append(QStandardItem(song['title']))
			else:
				items.append(QStandardItem("Unk. Title"))
			if 'artist' in song:
				items.append(QStandardItem(song['artist']))
			else:
				items.append(QStandardItem("Unk. Artist"))
			for item in items:
				item.setData(song)
			self.albumTrackListModel.appendRow(items)
		self.currentAlbum = albumdeets

	def startAlbumArtLoad(self, handle, aid):
		loader = albumArtLoader(handle, aid)
		loader.signals.albumArtLoaded.connect(self.displayAlbumArt)
		self.albumArtLoaderThreads.start(loader)

	def displayAlbumArt(self, art, aid):
		if aid == self.currentAlbum['coverArt']:
			image = QImage()
			image.loadFromData(art)
			self.ui.selectedAlbumArt.setPixmap(QPixmap.fromImage(image))

	def refreshAlbumListView(self):
		self.loadDataforAlbumListView(self.albumListState)

	def openAlbumTrackListMenu(self, position):
		if len(self.ui.albumTrackList.selectedIndexes()) > 0:
			menu = QMenu()
			playTracksNextAction = menu.addAction('Play Next')
			playTracksLastAction = menu.addAction('Play Last')
			action = menu.exec_(self.ui.albumTrackList.mapToGlobal(position))
			if action == playTracksNextAction or action == playTracksLastAction:
				songs = []
				for item in self.ui.albumTrackList.selectedIndexes():
					if item.column() == 0:
						songs.append(self.albumTrackListModel.itemFromIndex(item).data())
				if action == playTracksNextAction:
					self.playbackController.addSongs(songs, afterCurrent=True)
				else:
					self.playbackController.addSongs(songs, afterCurrent=False)

	def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
		print('Airsonic desktop closing, saving config')
		config.save()

if __name__ == "__main__":
	app = QApplication([])
	window = MainWindow()
	window.show()
	app.exec_()
