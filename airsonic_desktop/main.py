from datetime import timedelta

import keyboard
from PyQt5.QtCore import QThread, pyqtSlot, QModelIndex, pyqtSignal, QObject, QSize, QThreadPool, \
	Qt, QItemSelectionModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QStyle, QAbstractItemView, QShortcut

import actions

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
	loadAlbumsOfType = pyqtSignal(str, int)
	loadAlbumWithId = pyqtSignal(str, object)
	loadAlbumArtWithId = pyqtSignal(str)
	playbackControl = pyqtSignal(str)
	getPlaylists = pyqtSignal()
	loadPlaylistSongs = pyqtSignal(str, object)
	addSongsToPlaylist = pyqtSignal(str, object)
	beginSearch = pyqtSignal(str, int)
	loadAlbumsForArtist = pyqtSignal(str, object)


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
		self.signals.loadAlbumsOfType.connect(self.networkWorker.getDataForAlbumTreeView)
		self.signals.loadAlbumWithId.connect(self.networkWorker.loadAlbumWithId)
		self.networkWorker.returnAlbumSongs.connect(self.receiveLoadedSongs)
		self.signals.loadAlbumArtWithId.connect(self.networkWorker.getAlbumArtWithId)
		self.networkWorker.returnAlbumArtHandle.connect(self.startAlbumArtLoad)
		self.signals.getPlaylists.connect(self.networkWorker.getPlaylists)
		self.networkWorker.returnPlaylists.connect(self.receivePlaylists)
		self.signals.loadPlaylistSongs.connect(self.networkWorker.getPlaylistSongs)
		self.networkWorker.returnPlaylistSongs.connect(self.receiveLoadedSongs)
		self.signals.addSongsToPlaylist.connect(self.networkWorker.addSongsToPlaylist)
		self.signals.beginSearch.connect(self.networkWorker.beginSearch)
		self.networkWorker.returnSearchResults.connect(self.receiveSearchResults)
		self.signals.loadAlbumsForArtist.connect(self.networkWorker.loadAlbumsForArtist)
		self.networkWorker.returnArtistAlbums.connect(self.receiveArtistAlbums)
		self.networkWorker.returnArtists.connect(self.receiveArtists)

		self.currentAlbum = None
		self.albumArtLoaderThreads = QThreadPool()
		self.albumListState = 'home'
		self.possibleAlbumListStates = {  # state name and whether it's pagable
			'home': False,
			'alphabeticalByName': True,
			'artists': False,
			'frequent': True,
			'newest': True,
			'recent': True,
			'random': True,
			'search': True
		}
		self.currentPage = 0

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

	def setIconForRepeatButton(self):
		if config.repeatList == "1":
			self.ui.repeatPlayQueueButton.setIcon(QIcon('icons/baseline-repeat-one.svg'))
			self.ui.repeatPlayQueueButton.setChecked(True)
		elif config.repeatList == True:
			self.ui.repeatPlayQueueButton.setIcon(QIcon('icons/baseline-repeat.svg'))
			self.ui.repeatPlayQueueButton.setChecked(True)
		else:
			self.ui.repeatPlayQueueButton.setIcon(QIcon('icons/baseline-repeat.svg'))
			self.ui.repeatPlayQueueButton.setChecked(False)

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
		# followPlayedTrackIcon.addFile('icons/baseline-location-disabled.svg', mode=QIcon.Active)
		# followPlayedTrackIcon.addFile('icons/baseline-my-location.svg', mode=QIcon.Normal)
		self.ui.toggleFollowPlayedTrackButton.setIcon(QIcon('icons/baseline-my-location.svg'))
		self.ui.volumeSliderLabel.setPixmap(QIcon('icons/baseline-volume-up.svg').pixmap(QSize(32, 32)))
		self.setIconForRepeatButton()

	def populateLeftPanel(self):
		# Populate Left Panel
		self.albumTreeListModel = QStandardItemModel()
		self.ui.backHomeButtonLayout.close()
		self.ui.search.returnPressed.connect(self.beginSearch)

		self.ui.albumTreeList.setModel(self.albumTreeListModel)
		self.ui.albumTreeList.setHeaderHidden(False)
		self.ui.albumTreeList.clicked[QModelIndex].connect(self.albumListClick)
		self.ui.albumTreeList.doubleClicked[QModelIndex].connect(self.albumListDoubleClick)
		self.ui.albumTreeList.expanded.connect(self.handleExpandedAlbumListViewItem)
		self.ui.albumTreeList.setAlternatingRowColors(True)
		self.albumTreeListModel.setColumnCount(2)

		self.ui.albumTreeList.setUniformRowHeights(True)
		self.ui.albumTreeList.setColumnWidth(0, 300)

		self.ui.backHomeButton.clicked.connect(self.backHome)
		self.ui.albumListViewPreviousPage.clicked.connect(self.previousPage)
		self.ui.albumListViewNextPage.clicked.connect(self.nextPage)
		self.ui.albumListViewRefresh.clicked.connect(self.refreshAlbumListView)
		self.backHome()

		# actions, menu setup
		self.ui.albumTreeList.setContextMenuPolicy(Qt.CustomContextMenu)
		self.ui.albumTreeList.customContextMenuRequested.connect(self.albumTreeListMenu)

	def refreshActions(self):
		# stores the actions used with each type of object in this list.
		self.albumTreeListActions = {
			'addToQueue': [actions.playNextAction(self, self.ui.albumTreeList),
						   actions.playLastAction(self, self.ui.albumTreeList)],
			'addToPlaylist': [actions.addToPlaylistMenu(self, self.ui.albumTreeList)]
			# TODO: Actions should be refreshed when a new playlist is added.
		}
		self.albumTrackListActions = {
			'addToQueue': [actions.playNextAction(self, self.ui.albumTrackList),
						   actions.playLastAction(self, self.ui.albumTrackList)],
			'addToPlaylist': [actions.addToPlaylistMenu(self, self.ui.albumTrackList)]
			# TODO: Actions should be refreshed when a new playlist is added.
		}
		self.playQueueActions = [actions.goToAlbumAction(self, self.ui.playQueueList),
								 actions.removeFromQueue(self, self.ui.playQueueList),
								 actions.addToPlaylistMenu(self, self.ui.albumTrackList)]

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
		self.ui.albumTrackList.customContextMenuRequested.connect(self.albumTrackListMenu)
		self.refreshActions()

	# noinspection PyArgumentList
	def populatePlayQueue(self):
		# populate play queue
		# define playbackController and connect it up
		self.playbackController = playbackController(self.networkWorker)
		self.ui.playQueueList.setModel(self.playbackController.playQueueModel)
		self.ui.playQueueList.doubleClicked.connect(self.playbackController.playSongFromQueue)
		self.playbackController.updatePlayerUI.connect(self.updatePlayerUI)
		self.signals.playbackControl.connect(self.playbackController.playbackControl)

		# connect play controls

		self.ui.playPause.clicked.connect(self.playbackController.playPause)
		self.ui.nextTrack.clicked.connect(self.playbackController.playNextSongExplicitly)
		self.ui.prevTrack.clicked.connect(self.playbackController.playPreviousSong)
		self.ui.stop.clicked.connect(self.playbackController.stop)
		self.ui.trackProgressBar.valueChanged.connect(self.playbackController.setTrackProgress)
		self.ui.trackProgressBar.sliderPressed.connect(self.trackSliderPressed)
		self.ui.trackProgressBar.sliderReleased.connect(self.trackSliderReleased)
		self.sliderBeingDragged = False
		self.ui.toggleFollowPlayedTrackButton.setChecked(config.followPlaybackInQueue)
		self.followPlayedTrack = config.followPlaybackInQueue
		self.ui.toggleFollowPlayedTrackButton.clicked.connect(self.updateFollowPlayedTrack)
		self.ui.shufflePlayqueueButton.clicked.connect(self.playbackController.shufflePlayQueue)
		self.ui.volumeSlider.valueChanged.connect(self.playbackController.setVolume)
		self.ui.volumeSlider.setValue(config.volume)
		self.ui.repeatPlayQueueButton.clicked.connect(self.changeRepeatState)
		self.ui.playQueueList.setContextMenuPolicy(Qt.CustomContextMenu)
		self.ui.playQueueList.customContextMenuRequested.connect(self.playQueueMenu)
		self.short1 = QShortcut(Qt.Key_Delete, self.ui.playQueueList, context=Qt.WidgetShortcut,
								activated=self.playQueueActions[1].removeFromQueue)
		self.short2 = QShortcut(Qt.Key_Enter, self.ui.playQueueList, context=Qt.WidgetShortcut,
								activated=self.playSelectedSongFromQueue)
		self.short3 = QShortcut(Qt.Key_Return, self.ui.playQueueList, context=Qt.WidgetShortcut,
								activated=self.playSelectedSongFromQueue)
		self.short4 = QShortcut(Qt.Key_Space, self.ui.playQueueList, context=Qt.ApplicationShortcut,
								activated=self.playbackController.playPause)

		# configure the play queue itself

		self.ui.playQueueList.setAlternatingRowColors(True)

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

	def trackSliderPressed(self):
		self.sliderBeingDragged = True

	def trackSliderReleased(self):
		self.sliderBeingDragged = False

	def nextPage(self):
		self.currentPage += 1
		self.refreshAlbumListView()

	def previousPage(self):
		self.currentPage -= 1
		self.refreshAlbumListView()

	def changeRepeatState(self):
		if config.repeatList == "1":
			config.repeatList = False
		elif config.repeatList == False:
			config.repeatList = True
		elif config.repeatList == True:
			config.repeatList = '1'
		self.setIconForRepeatButton()

	@pyqtSlot(object, str)
	def updatePlayerUI(self, update, type):
		if type == 'total':
			self.ui.trackProgressBar.blockSignals(True)
			self.ui.trackProgressBar.setRange(0, update)
			if self.taskbarProgress:
				self.taskbarProgress.setMaximum(update)
			self.ui.trackProgressBar.blockSignals(False)
		elif type == 'progress':
			if not self.sliderBeingDragged:
				self.ui.trackProgressBar.blockSignals(True)
				self.ui.trackProgressBar.setValue(update)
				self.ui.trackProgressBar.blockSignals(False)
			if self.taskbarProgress:
				self.taskbarProgress.setValue(update)
		elif type == 'title':
			self.ui.currentPlayingLabel.setText(update)
		elif type == 'artist':
			self.ui.trackArtistName.setText(update)
		elif type == 'statusBar':
			self.statusBar().showMessage(update)
		elif type == 'scrollTo':
			if self.followPlayedTrack:
				self.ui.playQueueList.scrollTo(update, QAbstractItemView.PositionAtTop)
				self.ui.playQueueList.selectionModel().select(update, QItemSelectionModel.ClearAndSelect)
		elif type == 'idle':
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
		if config.followPlaybackInQueue:
			self.followPlayedTrack = False
		# self.ui.toggleFollowPlayedTrackButton.setChecked(False)
		else:
			self.followPlayedTrack = True

	# self.ui.toggleFollowPlayedTrackButton.setChecked(True)

	def playSelectedSongFromQueue(self):
		print('playing song from queue')
		indexes = self.ui.playQueueList.selectedIndexes()
		if len(indexes) > 0:
			self.playbackController.playSongFromQueue(indexes[0])

	def playPause(self):
		print('playPause hotkey hit')
		self.signals.playbackControl.emit('playPause')

	def albumListClick(self, index):
		item = self.albumTreeListModel.itemFromIndex(index)
		text = item.text()
		data = item.data()
		if not data:
			return  # this item isn't meant to be clicked on
		print('{} clicked, attempting load...'.format(text))
		if data['type'] == 'category':
			self.loadDataforAlbumListView(text)
		elif data['type'] == 'playlist':
			self.loadPlaylistSongs(item.data())
		elif data['type'] == 'album':
			data = item.data()['id']
			self.signals.loadAlbumWithId.emit(data, {'display': True,
													 'afterCurrent': False})

	def albumListDoubleClick(self, index):
		item = self.albumTreeListModel.itemFromIndex(index)
		text = item.text()
		data = item.data()
		print('{} dblclicked, attempting load...'.format(text))
		if data['type'] == 'song':
			self.playbackController.addSongs([data])

	def loadPlaylistSongs(self, item):
		self.signals.loadPlaylistSongs.emit(item['id'], {'display': True,
														 'afterCurrent': False})

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
					item.setData(playlist)
					items.append(item)
					item = QStandardItem(str(playlist['songCount']))
					item.setData(playlist)
					items.append(item)
					self.albumTreeListModel.appendRow(items)
			self.refreshActions()

	def beginSearch(self):
		query = self.ui.search.text()
		self.signals.beginSearch.emit(query, self.currentPage)

	def receiveSearchResults(self, results, page):
		self.changeAlbumListState('search')
		self.ui.albumTreeList.setIndentation(15)
		self.albumTreeListModel.setColumnCount(3)
		self.ui.albumTreeList.setHeaderHidden(False)
		self.ui.albumTreeList.setColumnWidth(0, 200)
		self.ui.albumTreeList.setColumnWidth(1, 200)
		self.albumTreeListModel.setHorizontalHeaderLabels(['Title', 'Album', 'Artist'])

		if 'song' in results:
			songContainer = QStandardItem('Songs')
			for item in results['song']:
				songContainer.appendRow(self.buildItemForSong(item, ['title', 'album', 'artist']))
			self.albumTreeListModel.appendRow(songContainer)
		if 'album' in results:
			albumContainer = QStandardItem('Albums')
			for item in results['album']:
				albumContainer.appendRow(self.buildItemForAlbum(item))
			self.albumTreeListModel.appendRow(albumContainer)
		if 'artist' in results:
			artistContainer = QStandardItem('Artists')
			for item in results['artist']:
				artistContainer.appendRow(self.buildItemForArtist(item))
			self.albumTreeListModel.appendRow(artistContainer)
		self.ui.albumTreeList.expandToDepth(0)

	def buildItemForArtist(self, artist):
		artistItem = QStandardItem(artist['name'])
		artistItem.setData(artist)
		loadingItem = QStandardItem('Loading')
		artistItem.appendRow(loadingItem)
		return artistItem

	def receiveArtists(self, artists):
		self.changeAlbumListState('artists')
		self.ui.albumTreeList.setIndentation(15)
		self.albumTreeListModel.setColumnCount(1)
		self.ui.albumTreeList.setHeaderHidden(True)
		artistIndexList = artists['artists']['index']
		for item in artistIndexList:
			index = QStandardItem(item['name'])
			for artist in item['artist']:
				index.appendRow(self.buildItemForArtist(artist))
			self.albumTreeListModel.appendRow(index)

	def handleExpandedAlbumListViewItem(self, index):
		item = self.albumTreeListModel.itemFromIndex(index)
		data = item.data()
		if data and 'type' in data and data['type'] == 'artist':
			print('loading artist {}'.format(item.data()))
			self.signals.loadAlbumsForArtist.emit(data['id'], index)

	def buildItemForAlbum(self, album):
		itemsList = [QStandardItem(album['name']), QStandardItem(album['artist'])]
		itemsList[0].setData(album)
		itemsList[1].setData(album)
		return itemsList

	def receiveArtistAlbums(self, albums, index):
		insertionPoint = self.albumTreeListModel.itemFromIndex(index)
		insertionPoint.removeRow(0)
		if albums and albums['artist'] and albums['artist']['album']:
			for item in albums['artist']['album']:
				insertionPoint.appendRow(self.buildItemForAlbum(item))

	def buildItemForSong(self, song, fields):
		items = []
		for field in fields:
			if field in song:
				items.append(QStandardItem(str(song[field])))
			else:
				items.append(QStandardItem("Unk. {}".format(field)))
		for item in items:
			item.setData(song)
		return items

	def loadDataforAlbumListView(self, type):
		type = type.lower()

		if type == 'playlists':
			self.signals.getPlaylists.emit()
			return
		if type == "recently added":
			type = 'newest'
		elif type == "recently played":
			type = 'recent'
		elif type == 'albums':
			type = 'alphabeticalByName'
		elif type == 'frequently played':
			type = 'frequent'
		self.changeAlbumListState(type)
		self.signals.loadAlbumsOfType.emit(type, self.currentPage)

	def albumTrackListDoubleClick(self, index):
		item = self.albumTrackListModel.itemFromIndex(index)
		text = item.text()
		print('{} dblclicked in track list, adding to play queue'.format(text))
		self.playbackController.playNow(self.currentAlbum['song'], item.data())

	def setPagableState(self, state):
		self.ui.albumListViewNextPage.setEnabled(state)
		self.ui.albumListViewPreviousPage.setEnabled(state)

	def changeAlbumListState(self, state):
		if state not in self.possibleAlbumListStates:
			raise ValueError('Invalid album list state selected')
		self.albumListState = state
		self.setPagableState(self.possibleAlbumListStates[state])
		if self.possibleAlbumListStates[state]:
			self.ui.albumTreeListTitle.setText('{} Page {}'.format(state.title(), self.currentPage + 1))
		else:
			self.ui.albumTreeListTitle.setText('{}'.format(state.title()))
		self.albumTreeListModel.clear()
		if state != 'home':
			self.ui.backHomeButtonLayout.setHidden(False)
		else:
			self.ui.backHomeButtonLayout.setHidden(True)

	@pyqtSlot()
	def backHome(self):
		self.changeAlbumListState('home')
		self.albumTreeListModel.setColumnCount(1)
		self.ui.albumTreeList.setIndentation(0)
		self.currentPage = 0
		self.ui.albumTreeList.setHeaderHidden(True)
		for item in ['Playlists', 'Random', 'Recently Added', 'Recently Played',
					 'Frequently Played', 'Artists', 'Albums', 'Folders']:
			standardItem = QStandardItem(item)
			standardItem.setData({'type': 'category'})
			self.albumTreeListModel.appendRow(standardItem)

	@pyqtSlot(object, str)
	def displayLoadedAlbums(self, albums, albumType):
		self.albumTreeListModel.setHorizontalHeaderLabels(["Album", "Artists"])
		self.ui.albumTreeList.setHeaderHidden(False)
		for item in albums['albumList2']['album']:
			self.albumTreeListModel.appendRow(self.buildItemForAlbum(item))
		self.ui.albumTreeList.setColumnWidth(0, 250)

	def playlistFromCacheById(self, id):
		for item in self.playlistCache:
			if item['id'] == id:
				return item
		return None

	@pyqtSlot(object, object)
	def receiveLoadedSongs(self, songContainer, addToQueue):
		if addToQueue['display'] == False:
			if songContainer['type'] == 'album':
				self.playbackController.addSongs(songContainer['song'],
												 afterCurrent=addToQueue['afterCurrent'])
			elif songContainer['type'] == 'playlist':
				self.playbackController.addSongs(songContainer['playlist']['entry'],
												 afterCurrent=songContainer['afterCurrent'])
			return
		songs = []
		if songContainer['type'] == 'album':
			albumdeets = songContainer
			songs = albumdeets['song']
		elif songContainer['type'] == 'playlist':
			print(songContainer)
			songs = songContainer['playlist']['entry']
			albumdeets = {}
			albumdeets['name'] = songContainer['playlist']['name']
			albumdeets['artist'] = ''
			albumdeets['songCount'] = len(songs)
			albumdeets['duration'] = self.playlistFromCacheById(songContainer['playlist']['id'])['duration']
			albumdeets['coverArt'] = self.playlistFromCacheById(songContainer['playlist']['id'])['coverArt']
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
			self.albumTrackListModel.appendRow(self.buildItemForSong(song,
																	 ['track',
																	  'title',
																	  'artist']))
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

	def albumTreeListMenu(self, position):
		self.openAlbumTreeOrListMenu(position, self.ui.albumTreeList, self.albumTreeListActions)

	def albumTrackListMenu(self, position):
		self.openAlbumTreeOrListMenu(position, self.ui.albumTrackList, self.albumTrackListActions)

	def playQueueMenu(self, position):
		if len(self.ui.playQueueList.selectedIndexes()) > 0:
			menu = QMenu()
			for item in self.playQueueActions:
				try:
					menu.addAction(item)
				except TypeError:
					menu.addMenu(item)
			menu.exec_(self.ui.playQueueList.mapToGlobal(position))

	def openAlbumTreeOrListMenu(self, position, list, actionsDict):
		if len(list.selectedIndexes()) > 0:
			menu = QMenu()
			items = actions.getItemsFromList(list)
			queueSongsActionsAdded = False
			playlistAddActionsAdded = False
			for item in items:
				if not queueSongsActionsAdded and \
						item['type'] == 'song' or \
						item['type'] == 'album':
					queueSongsActionsAdded = True
					menu.addActions(actionsDict['addToQueue'])
				if not playlistAddActionsAdded and item['type'] == 'song':
					playlistAddActionsAdded = True
					menu.addMenu(actionsDict['addToPlaylist'][0])
			menu.exec_(list.mapToGlobal(position))


def closeEvent(self, a0):
	print('Airsonic desktop closing, saving config')
	config.save()


if __name__ == "__main__":
	app = QApplication([])
	window = MainWindow()
	window.show()
	app.exec_()
