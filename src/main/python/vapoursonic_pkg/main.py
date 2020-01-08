import os
import sys
from _md5 import md5
from datetime import timedelta

from PyQt5.QtCore import QThread, pyqtSlot, QModelIndex, pyqtSignal, QObject, QSize, QThreadPool, \
	Qt, QItemSelectionModel, QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPixmap, QImage, QGuiApplication, QIntValidator, QCursor
from PyQt5.QtWidgets import QMainWindow, QMenu, QStyle, QAbstractItemView, QShortcut, QMessageBox, QLabel
from fbs_runtime.application_context.PyQt5 import ApplicationContext

from vapoursonic_pkg.widgets.messagePopup import toastMessageDisplay
from vapoursonic_pkg.config import config
from vapoursonic_pkg.albumArtLoader import albumArtLoader
from vapoursonic_pkg.networkWorker import networkWorker
from vapoursonic_pkg.playbackController import playbackController
from vapoursonic_pkg.widgets.ui_mainwindow import Ui_vapoursonic
from vapoursonic_pkg import vapoursonicActions
from vapoursonic_pkg.widgets import settingsPanel
from vapoursonic_pkg.widgets.albumArtViewer import albumArtViewer


class MainWindowSignals(QObject):
	loadAlbumsOfType = pyqtSignal(str, int)
	loadAlbumWithId = pyqtSignal(str, object)
	playbackControl = pyqtSignal(str)
	getPlaylists = pyqtSignal()
	loadPlaylistSongs = pyqtSignal(str, object)
	addSongsToPlaylist = pyqtSignal(str, object)
	beginSearch = pyqtSignal(str, int)
	loadAlbumsForArtist = pyqtSignal(str, object)
	resized = pyqtSignal()
	artAvailableForCurrentSong = pyqtSignal()
	loadMusicFolder = pyqtSignal(str)
	loadRootMusicFolder = pyqtSignal()


def openAlbumTreeOrListMenu(position, focusedList, actionsDict):
	if len(focusedList.selectedIndexes()) > 0:
		menu = QMenu()
		items = vapoursonicActions.getItemsFromList(focusedList)
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
		menu.exec_(QCursor.pos())


def buildItemForArtist(artist):
	artistItem = QStandardItem(artist['name'])
	artistItem.setData(artist)
	loadingItem = QStandardItem('Loading')
	artistItem.appendRow(loadingItem)
	return artistItem


def buildItemForAlbum(album):
	itemsList = [QStandardItem(album['name']), QStandardItem(album['artist'])]
	itemsList[0].setData(album)
	itemsList[1].setData(album)
	return itemsList


def showSettings():
	dialog = settingsPanel.settingsDialog()


def initConnectionParams():
	config.salt = md5(os.urandom(100)).hexdigest()
	config.token = md5((config.password + config.salt).encode('utf-8')).hexdigest()


class MainWindow(QMainWindow):

	def __init__(self, appContext, *args, **kwargs):
		super(MainWindow, self).__init__(*args, **kwargs)
		self.appContext = appContext
		self.networkThread = QThread()
		self.networkWorker = networkWorker()
		self.networkWorker.moveToThread(self.networkThread)
		self.networkThread.start()
		self.ui = Ui_vapoursonic()

		self.ui.setupUi(self)

		self.populateConnectFields()

		self.ui.stackedWidget.setCurrentIndex(0)

		self.signals = MainWindowSignals()
		self.toastDisplay = toastMessageDisplay(self)
		self.ui.connectButton.clicked.connect(lambda: self.networkWorker.connectToServer(
			self.ui.domainInput.text(),
			self.ui.usernameInput.text(),
			self.ui.passwordInput.text()
		))
		self.ui.actionSettings.triggered.connect(showSettings)
		self.ui.autoConnectCheckBox.stateChanged.connect(settingsPanel.setAutoConnectState)
		self.networkWorker.returnAlbums.connect(self.receiveAlbumList)
		self.networkWorker.connectResult.connect(self.connectResult)
		self.signals.loadAlbumsOfType.connect(self.networkWorker.getDataForAlbumTreeView)
		self.signals.loadAlbumWithId.connect(self.networkWorker.loadAlbumWithId)
		self.networkWorker.returnAlbumSongs.connect(self.receiveLoadedSongs)
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
		self.networkWorker.errorHandler.connect(self.handleError)
		self.networkWorker.showMessageBox.connect(self.toastDisplay.showMessage)
		self.networkWorker.returnMusicFolder.connect(self.receiveMusicFolder)
		self.signals.loadMusicFolder.connect(self.networkWorker.loadMusicFolder)
		self.signals.loadRootMusicFolder.connect(self.networkWorker.loadRootMusicFolders)
		self.networkWorker.returnRootMusicFolders.connect(self.receiveRootMusicFolders)
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
			'search': True,
			'playlists': True,
			'folders': False
		}
		self.currentPage = 0
		self.albumArtCache = {}
		if config.autoConnect:
			self.ui.connectButton.click()

	# it just werkz!

	def populateConnectFields(self):
		self.ui.domainInput.setText(config.domain)
		self.ui.usernameInput.setText(config.username)
		self.ui.passwordInput.setText(config.password)
		self.ui.autoConnectCheckBox.setChecked(config.autoConnect)
		self.ui.useTLSCheckBox.setChecked(config.useTLS)
		self.ui.useCustomPortCheckBox.setChecked(config.useCustomPort)
		self.ui.customPortLineEdit.setEnabled(config.useCustomPort)
		self.ui.customPortLineEdit.setText(str(config.customPort))
		self.ui.customPortLineEdit.setValidator(QIntValidator())
	def resizeEvent(self, newSize):
		self.signals.resized.emit()
		QMainWindow.resizeEvent(self, newSize)

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
			self.handleError(
				'Unable to connect to your server. Please check your domain and credentials and try again.')

	# should slap an error somewhere lol

	def setIconForRepeatButton(self):
		if config.repeatList == "1":
			self.ui.repeatPlayQueueButton.setIcon(config.icons['baseline-repeat-one.svg'])
			self.ui.repeatPlayQueueButton.setChecked(True)
		elif config.repeatList:
			self.ui.repeatPlayQueueButton.setIcon(config.icons['baseline-repeat.svg'])
			self.ui.repeatPlayQueueButton.setChecked(True)
		else:
			self.ui.repeatPlayQueueButton.setIcon(config.icons['baseline-repeat.svg'])
			self.ui.repeatPlayQueueButton.setChecked(False)

	def populateIcons(self):
		# Populate icons
		self.playIcon = config.icons['baseline-play-arrow.svg']
		self.pauseIcon = config.icons['baseline-pause.svg']
		self.ui.nextTrack.setIcon(config.icons['baseline-skip-next.svg'])
		self.ui.prevTrack.setIcon(config.icons['baseline-skip-previous.svg'])
		self.ui.playPause.setIcon(self.playIcon)
		self.ui.search.setClearButtonEnabled(True)
		countIconPixmap = config.icons['audio-spectrum.svg'].pixmap(QSize(24, 24))
		lengthIconPixmap = config.icons['baseline-access-time.svg'].pixmap(QSize(24, 24))
		yearIconPixmap = config.icons['sharp-date-range.svg'].pixmap(QSize(24, 24))
		self.ui.selectedAlbumReleaseYearIcon.setPixmap(yearIconPixmap)
		self.ui.selectedAlbumTrackCountIcon.setPixmap(countIconPixmap)
		self.ui.selectedAlbumTotalLengthIcon.setPixmap(lengthIconPixmap)
		self.ui.albumListViewPreviousPage.setIcon(config.icons['baseline-navigate-before.svg'])
		self.ui.albumListViewPreviousPage.setText('')
		self.ui.albumListViewNextPage.setIcon(config.icons['baseline-navigate-next.svg'])
		self.ui.albumListViewNextPage.setText('')
		self.ui.albumListViewRefresh.setIcon(config.icons['baseline-refresh.svg'])
		self.ui.albumListViewRefresh.setText('')
		self.ui.backHomeButton.setIcon(config.icons['baseline-arrow-back.svg'])
		self.ui.backHomeButton.setStyleSheet('QPushButton { text-align: left; }')
		self.ui.shufflePlayqueueButton.setIcon(config.icons['baseline-shuffle.svg'])
		# followPlayedTrackIcon.addFile('icons' + os.path.sep + 'baseline-location-disabled.svg', mode=QIcon.Active)
		# followPlayedTrackIcon.addFile('icons' + os.path.sep + 'baseline-my-location.svg', mode=QIcon.Normal)
		self.ui.toggleFollowPlayedTrackButton.setIcon(config.icons['baseline-my-location.svg'])
		self.ui.volumeSliderLabel.setPixmap(config.icons['baseline-volume-up.svg'].pixmap(QSize(32, 32)))
		self.ui.clearPlaylistButton.setIcon(config.icons['baseline-delete-outline.svg'])
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
			'addToQueue': [vapoursonicActions.playNextAction(self, self.ui.albumTreeList),
			               vapoursonicActions.playLastAction(self, self.ui.albumTreeList)],
			'addToPlaylist': [vapoursonicActions.addToPlaylistMenu(self, self.ui.albumTreeList)]
			# TODO: Actions should be refreshed when a new playlist is added.
		}
		self.albumTrackListActions = {
			'addToQueue': [vapoursonicActions.playNextAction(self, self.ui.albumTrackList),
			               vapoursonicActions.playLastAction(self, self.ui.albumTrackList)],
			'addToPlaylist': [vapoursonicActions.addToPlaylistMenu(self, self.ui.albumTrackList)]
			# TODO: Actions should be refreshed when a new playlist is added.
		}
		self.playQueueActions = [vapoursonicActions.goToAlbumAction(self, self.ui.playQueueList),
		                         vapoursonicActions.removeFromQueue(self, self.ui.playQueueList),
		                         vapoursonicActions.addToPlaylistMenu(self, self.ui.playQueueList)]

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
		self.ui.selectedAlbumArt.mouseReleaseEvent = self.displayFullAlbumArtForBrowsing
		self.refreshActions()

	# noinspection PyArgumentList
	def populatePlayQueue(self):
		# define playbackController and connect it up
		self.playbackController = playbackController()
		self.playbackController.volumeSet.connect(lambda vol: self.ui.volumeSlider.setValue(vol))
		self.ui.playQueueList.setModel(self.playbackController.playQueueModel)
		self.ui.playQueueList.doubleClicked.connect(self.playbackController.playSongFromQueue)
		self.playbackController.updatePlayerUI.connect(self.updatePlayerUI)
		self.playbackController.idleUpdate.connect(self.idleUpdate)
		self.signals.playbackControl.connect(self.playbackController.playbackControl)

		# connect play controls

		self.ui.playPause.clicked.connect(self.playbackController.playPause)
		self.ui.nextTrack.clicked.connect(self.playbackController.playNextSongExplicitly)
		self.ui.prevTrack.clicked.connect(self.playbackController.playPreviousSong)
		self.playbackController.trackProgressUpdate.connect(self.ui.trackProgressBar.progressUpdate)
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
		self.ui.clearPlaylistButton.clicked.connect(self.playbackController.clearPlayQueue)
		self.ui.playingAlbumArt.mouseReleaseEvent = self.displayFullAlbumArtForPlaying

		self.short1 = QShortcut(Qt.Key_Delete, self.ui.playQueueList, context=Qt.WidgetShortcut,
		                        activated=self.playQueueActions[1].removeFromQueue)
		self.short2 = QShortcut(Qt.Key_Enter, self.ui.playQueueList, context=Qt.WidgetShortcut,
		                        activated=self.ui.playQueueList.playSelectedSongFromQueue)
		self.short3 = QShortcut(Qt.Key_Return, self.ui.playQueueList, context=Qt.WidgetShortcut,
		                        activated=self.ui.playQueueList.playSelectedSongFromQueue)
		self.short4 = QShortcut(Qt.Key_Space, self.ui.playQueueList, context=Qt.ApplicationShortcut,
		                        activated=self.playbackController.playPause)
		# configure the play queue itself
		self.ui.playQueueList.setAlternatingRowColors(True)

	def initializeWindowsIntegration(self):
		from vapoursonic_pkg import windowsIntegration
		from PyQt5.QtWinExtras import QWinTaskbarProgress, QWinTaskbarButton, QWinThumbnailToolBar, \
			QWinThumbnailToolButton
		self.keyHookThreadPool = QThreadPool()
		self.keyHookThreadPool.setMaxThreadCount(1)
		self.keyHook = windowsIntegration.mediaKeysHooker(self)
		self.keyHook.signals.playPauseSignal.connect(self.playbackController.playPause)
		self.keyHook.signals.nextSongSignal.connect(self.playbackController.playNextSongExplicitly)
		self.keyHook.signals.prevSongSignal.connect(self.playbackController.playPreviousSong)
		self.keyHook.signals.errSignal.connect(self.toastDisplay.showMessage)
		self.keyHookThreadPool.start(self.keyHook)

		if QWinTaskbarProgress:
			self.taskbarProgressBar = windowsIntegration.taskbarProgressBar(self)
			self.taskbarProgressBar.playToolbarButton.clicked.connect(self.playbackController.playPause)
			self.taskbarProgressBar.prevToolbarButton.clicked.connect(self.playbackController.playPreviousSong)
			self.taskbarProgressBar.nextToolbarButton.clicked.connect(self.playbackController.playNextSongExplicitly)
			self.playbackController.idleUpdate.connect(self.taskbarProgressBar.updatePlayButtonIcon)
			self.playbackController.trackProgressUpdate.connect(self.taskbarProgressBar.updateProgressBar)
			self.signals.artAvailableForCurrentSong.connect(self.taskbarProgressBar.artAvailable)
		else:
			self.taskbarProgress = None

	# self.mediaTransportControls = windowsIntegration.systemMediaTransportControls()

	def cachePlaylists(self):
		self.signals.getPlaylists.emit()

	def loadPlayQueue(self):
		if config.playQueueState['queueServer'] and \
				config.playQueueState['queueServer'] == config.username + "@" + config.domain:
			queue = config.playQueueState['queue']
			self.playbackController.addSongs(queue, queue[config.playQueueState['currentIndex']])
			self.playbackController.playPause()

	def initializeLinuxIntegration(self):
		from vapoursonic_pkg import linuxIntegration
		self.mprisIntegration = linuxIntegration.mprisIntegration(self.playbackController)

	def populatePlayerUI(self):
		initConnectionParams()

		self.populateIcons()

		self.populateLeftPanel()

		self.populateRightPanel()

		self.populatePlayQueue()

		if sys.platform == 'win32':
			timer = QTimer(self)
			timer.timeout.connect(lambda: self.initializeWindowsIntegration())
			timer.setSingleShot(True)
			timer.start(0)
		elif sys.platform == 'linux':
			self.initializeLinuxIntegration()

		self.cachePlaylists()

		self.loadPlayQueue()

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
		elif not config.repeatList:
			config.repeatList = True
		elif config.repeatList:
			config.repeatList = '1'
		self.setIconForRepeatButton()

	def handleError(self, error):
		QMessageBox.information(self, 'Error', error)
		print(error)

	@pyqtSlot(object, str)
	def updatePlayerUI(self, update, updateType):
		if updateType == "progressText":
			self.ui.trackProgressIndicator.setText(update)
		elif updateType == "newCurrentSong":
			if update:
				self.ui.currentPlayingLabel.setText(update['title'])
				self.ui.currentPlayingLabel.setToolTip(update['title'])
				self.ui.trackArtistName.setText(update['artist'])
				self.ui.trackArtistName.setToolTip(update['artist'])

				self.setWindowTitle("{} by {} - {}".format(update['title'] if 'title' in update else 'Unk. Title',
				                                           update['artist'] if 'artist' in update else 'Unk. Artist',
				                                           config.appname))
				if 'coverArt' in update:
					self.beginDisplayAlbumArt(update['coverArt'], 'currentlyPlaying')
				else:
					self.clearAlbumArt('currentlyPlaying')
			else:
				self.ui.currentPlayingLabel.setText('Not Playing')
				self.ui.currentPlayingLabel.setToolTip('Not Playing')
				self.ui.trackArtistName.setText('No Artist')
				self.ui.trackArtistName.setToolTip('No Artist')
				self.setWindowTitle('Not Playing - {}'.format(config.appname))
		elif updateType == 'statusBar':
			self.statusBar().showMessage(update)
		elif updateType == 'scrollTo':
			if self.followPlayedTrack:
				self.ui.playQueueList.scrollTo(update, QAbstractItemView.PositionAtTop)
				self.ui.playQueueList.selectionModel().select(update,
				                                              QItemSelectionModel.ClearAndSelect |
				                                              QItemSelectionModel.Rows)

	def idleUpdate(self, paused):
		if paused:
			self.ui.playPause.setIcon(self.playIcon)
		else:
			self.ui.playPause.setIcon(self.pauseIcon)

	def updateFollowPlayedTrack(self):
		if config.followPlaybackInQueue:
			self.followPlayedTrack = False
		else:
			self.followPlayedTrack = True

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
		elif data['type'] == 'album':
			self.signals.loadAlbumWithId.emit(data['id'], {'display': False,
			                                               'afterCurrent': False,
			                                               'playNow': True})

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

	def getMusicFolderInsertionPoint(self, folderId):
		if self.albumListState == 'folders':
			for item in range(0, self.albumTreeListModel.rowCount()):
				row = self.albumTreeListModel.item(item, 0).data()
				if row and row['type'] == 'musicFolder':
					if row['id'] == folderId:
						return item

	def receiveMusicFolder(self, folders, folderId):
		insertionPoint = self.albumTreeListModel.item(
			self.getMusicFolderInsertionPoint(folderId), 0)
		for item in folders['directory']['child']:
			row = []
			standardItem = QStandardItem(item['title'])
			standardItem.setData(item)
			row.append(standardItem)
			standardItem = QStandardItem(item['album'])
			standardItem.setData(item)
			row.append(standardItem)
			insertionPoint.appendRow(row)
		self.refreshActions()

	def receiveRootMusicFolders(self, folders):
		self.ui.albumTreeList.setIndentation(15)
		self.albumTreeListModel.setColumnCount(2)
		self.ui.albumTreeList.setHeaderHidden(False)
		self.albumTreeListModel.setHorizontalHeaderLabels(['Title', 'Artist'])
		self.ui.albumTreeList.setColumnWidth(0, 200)
		self.ui.albumTreeList.setColumnWidth(1, 200)
		for item in folders['musicFolders']['musicFolder']:
			standardItem = QStandardItem(item['name'])
			standardItem.setData(item)
			self.albumTreeListModel.appendRow(standardItem)
			standardItem.appendRow(QStandardItem('Loading...'))
		self.refreshActions()


	def beginSearch(self):
		query = self.ui.search.text()
		self.signals.beginSearch.emit(query, self.currentPage)

	def receiveSearchResults(self, results):
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
				songContainer.appendRow(buildItemForSong(item, ['title', 'album', 'artist']))
			self.albumTreeListModel.appendRow(songContainer)
		if 'album' in results:
			albumContainer = QStandardItem('Albums')
			for item in results['album']:
				albumContainer.appendRow(buildItemForAlbum(item))
			self.albumTreeListModel.appendRow(albumContainer)
		if 'artist' in results:
			artistContainer = QStandardItem('Artists')
			for item in results['artist']:
				artistContainer.appendRow(buildItemForArtist(item))
			self.albumTreeListModel.appendRow(artistContainer)
		self.ui.albumTreeList.expandToDepth(0)

	def receiveArtists(self, artists):
		self.changeAlbumListState('artists')
		self.ui.albumTreeList.setIndentation(15)
		self.albumTreeListModel.setColumnCount(1)
		self.ui.albumTreeList.setHeaderHidden(True)
		artistIndexList = artists['artists']['index']
		for item in artistIndexList:
			index = QStandardItem(item['name'])
			for artist in item['artist']:
				index.appendRow(buildItemForArtist(artist))
			self.albumTreeListModel.appendRow(index)

	def handleExpandedAlbumListViewItem(self, index):
		item = self.albumTreeListModel.itemFromIndex(index)
		data = item.data()
		if data and 'type' in data and data['type'] == 'artist':
			print('loading artist {}'.format(item.data()))
			self.signals.loadAlbumsForArtist.emit(data['id'], index)
		if data and 'type' in data and data['type'] == 'rootMusicFolder':
			print('loading root music folder {}'.format(item.data()['name']))
			self.signals.loadMusicFolder.emit(str(item.data()['id']))

	def receiveArtistAlbums(self, albums, index):
		insertionPoint = self.albumTreeListModel.itemFromIndex(index)
		insertionPoint.removeRow(0)
		if albums and albums['artist'] and albums['artist']['album']:
			for item in albums['artist']['album']:
				insertionPoint.appendRow(buildItemForAlbum(item))

	def loadDataforAlbumListView(self, dataType):
		dataType = dataType.lower()

		if dataType == 'playlists':
			self.signals.getPlaylists.emit()
			self.changeAlbumListState(dataType)
			return
		if dataType == "recently added":
			dataType = 'newest'
		elif dataType == "recently played":
			dataType = 'recent'
		elif dataType == 'albums':
			dataType = 'alphabeticalByName'
		elif dataType == 'frequently played':
			dataType = 'frequent'
		self.changeAlbumListState(dataType)
		if dataType == 'folders':
			self.signals.loadRootMusicFolder.emit()
		else:
			self.signals.loadAlbumsOfType.emit(dataType, self.currentPage)

	def albumTrackListDoubleClick(self, index):
		item = self.albumTrackListModel.itemFromIndex(index)
		text = item.text()
		print('{} dblclicked in track list, playing now'.format(text))
		self.playbackController.addSongs(self.currentAlbum['song'], item.data())

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
	def receiveAlbumList(self, albums):
		self.albumTreeListModel.setHorizontalHeaderLabels(["Album", "Artists"])
		self.ui.albumTreeList.setHeaderHidden(False)
		for item in albums['albumList2']['album']:
			self.albumTreeListModel.appendRow(buildItemForAlbum(item))
		self.ui.albumTreeList.setColumnWidth(0, 250)

	def playlistFromCacheById(self, playlistId):
		for item in self.playlistCache:
			if item['id'] == playlistId:
				return item
		return None

	@pyqtSlot(object, object)
	def receiveLoadedSongs(self, songContainer, addToQueue):
		if not addToQueue['display']:
			if songContainer['type'] == 'album':
				if 'playNow' in addToQueue.keys() and addToQueue['playNow']:
					self.playbackController.addSongs(songContainer['song'],
					                                 songContainer['song'][0],
					                                 addToQueue['afterCurrent'])
				else:
					self.playbackController.addSongs(songContainer['song'],
					                                 afterCurrent=addToQueue['afterCurrent'])
			elif songContainer['type'] == 'playlist':
				if 'playNow' in addToQueue.keys() and addToQueue['playNow']:
					self.playbackController.addSongs(songContainer['playlist']['entry'],
					                                 songContainer['playlist']['entry'][0],
					                                 addToQueue['afterCurrent'])
				else:
					self.playbackController.addSongs(songContainer['playlist']['entry'],
					                                 afterCurrent=songContainer['afterCurrent'])
			return
		if songContainer['type'] == 'album':
			albumdeets = songContainer
			songs = albumdeets['song']
		elif songContainer['type'] == 'playlist':
			print(songContainer)
			songs = songContainer['playlist']['entry']
			albumdeets = {'name': songContainer['playlist']['name'],
			              'artist': '',
			              'songCount': len(songs),
			              'duration': self.playlistFromCacheById(songContainer['playlist']['id'])['duration'],
			              'coverArt': self.playlistFromCacheById(songContainer['playlist']['id'])['coverArt'],
			              'song': songs}
		else:
			raise Exception('incorrect songContainer type passed to receiveLoadedSongs()')

		self.albumTrackListModel.clear()
		self.albumTrackListModel.setHorizontalHeaderLabels(['Track No.', 'Title', 'Artist'])
		self.currentAlbum = albumdeets
		try:
			self.beginDisplayAlbumArt(albumdeets['coverArt'], 'album')
		except KeyError:
			self.clearAlbumArt('album')
		self.ui.selectedAlbumTitle.setText(albumdeets['name'])
		self.ui.selectedAlbumTitle.setToolTip(albumdeets['name'])
		self.ui.selectedAlbumArtist.setText(albumdeets['artist'])
		self.ui.selectedAlbumArtist.setToolTip(albumdeets['artist'])
		self.ui.selectedAlbumTrackCount.setText(str(albumdeets['songCount']))
		self.ui.selectedAlbumTotalLength.setText(str(timedelta(seconds=albumdeets['duration'])))
		try:
			self.ui.selectedAlbumReleaseYear.setText(str(albumdeets['year']))
		except KeyError:
			self.ui.selectedAlbumReleaseYear.setText('')
		for song in songs:
			self.albumTrackListModel.appendRow(buildItemForSong(song,
			                                                    ['track',
			                                                     'title',
			                                                     'artist']))

	def refreshAlbumListView(self):
		self.loadDataforAlbumListView(self.albumListState)

	def albumTreeListMenu(self, position):
		openAlbumTreeOrListMenu(position, self.ui.albumTreeList, self.albumTreeListActions)

	def albumTrackListMenu(self, position):
		openAlbumTreeOrListMenu(position, self.ui.albumTrackList, self.albumTrackListActions)

	def closeEvent(self, a0):
		print('vapoursonic closing, saving config')
		config.save(self.playbackController)
		sys.exit(0)

	def startAlbumArtLoad(self, aid, artType):
		loader = albumArtLoader(aid, artType)
		loader.signals.albumArtLoaded.connect(self.receiveAlbumArt)
		loader.signals.errorHandler.connect(self.handleError)
		self.albumArtLoaderThreads.start(loader)

	# noinspection PyCallByClass
	def receiveAlbumArt(self, art, aid, artType):
		image = QImage()
		image.loadFromData(art)
		self.albumArtCache[aid] = QPixmap.fromImage(image)
		self.displayAlbumArt(aid, artType)

	def beginDisplayAlbumArt(self, artId, artType):
		try:
			self.displayAlbumArt(artId, artType)
		except KeyError:
			self.startAlbumArtLoad(artId, artType)

	def clearAlbumArt(self, artType):
		if artType == 'album':
			self.ui.selectedAlbumArt.setText('No Art')
			self.ui.selectedAlbumArt.setCursor(Qt.ArrowCursor)
		elif artType == 'currentlyPlaying':
			self.ui.playingAlbumArt.setPixmap(QPixmap())
			self.ui.playingAlbumArt.setCursor(Qt.ArrowCursor)
			# print('emitting artAvailable as song has no art')
			self.signals.artAvailableForCurrentSong.emit()

	def displayAlbumArt(self, aid, artType):
		if artType == 'album' and aid == self.currentAlbum['coverArt']:
			self.ui.selectedAlbumArt.setCursor(Qt.PointingHandCursor)
			self.ui.selectedAlbumArt.setPixmap(self.albumArtCache[aid].
			                                   scaled(self.ui.selectedAlbumArt.size(),
			                                          Qt.KeepAspectRatio,
			                                          Qt.SmoothTransformation))
		elif artType == 'currentlyPlaying' and self.playbackController.currentSongData and \
				aid == self.playbackController.currentSongData['coverArt']:
			self.ui.playingAlbumArt.setCursor(Qt.PointingHandCursor)
			self.ui.playingAlbumArt.setPixmap(self.albumArtCache[aid].
			                                  scaled(self.ui.playingAlbumArt.size(),
			                                         Qt.KeepAspectRatio,
			                                         Qt.SmoothTransformation))
			# print('emitting artAvailable art is available for {}'.format(aid))
			self.signals.artAvailableForCurrentSong.emit()

	def displayFullAlbumArtForPlaying(self, _):
		self.displayFullAlbumArt('currentlyPlaying')

	def displayFullAlbumArtForBrowsing(self, _):
		self.displayFullAlbumArt('currentlyBrowsing')

	def displayFullAlbumArt(self, artType):
		if artType == 'currentlyPlaying' and self.playbackController.currentSong:
			dialog = albumArtViewer(self, self.playbackController.currentSong.data()['coverArt'],
			                        self.networkWorker)
		elif artType == 'currentlyBrowsing' and self.currentAlbum:
			dialog = albumArtViewer(self, self.currentAlbum['coverArt'],
			                        self.networkWorker)
		else:
			raise ValueError('Incorrect artType passed to displayFullAlbumArt')

		dialog.show()
		dialog.raise_()
		dialog.activateWindow()


def buildItemForSong(song, fields):
	items = []
	for field in fields:
		if field in song:
			items.append(QStandardItem(str(song[field])))
		else:
			items.append(QStandardItem("Unk. {}".format(field)))
	for item in items:
		item.setData(song)
	return items


if __name__ == "__main__":
	appcontext = ApplicationContext()
	appcontext.app.setAttribute(Qt.AA_UseHighDpiPixmaps)
	window = MainWindow(appcontext)
	window.show()
	appcontext.app.exec_()