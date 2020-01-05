from PyQt5.QtWidgets import QAction, QMenu

from vapoursonic_pkg.config import config


def getItemsFromList(focusedList):
	items = []
	selectedItems = focusedList.selectedIndexes()
	for item in selectedItems:
		if item.column() == 0:
			items.append(focusedList.model().itemFromIndex(item).data())
	return items


def addSongs(focusedList, parent, afterCurrent):
	items = getItemsFromList(focusedList)
	songs = []
	for item in items:
		if item['type'] == 'song':
			songs.append(item)
		elif item['type'] == 'album':
			parent.signals.loadAlbumWithId.emit(item['id'], {'display': False,
															 'afterCurrent': afterCurrent})
	if len(songs) > 0:
		parent.playbackController.addSongs(songs, afterCurrent=afterCurrent)


class playLastAction(QAction):
	def __init__(self, parent, focusedList):
		# print('init playLastAction')
		super(playLastAction, self).__init__(config.icons['baseline-queue.svg'], 'Add to Queue', parent)
		self.focusedList = focusedList
		self.triggered.connect(self.playLastTriggered)

	def playLastTriggered(self, checked):
		addSongs(self.focusedList, self.parent(), False)


class playNextAction(QAction):
	def __init__(self, parent, focusedList):
		# print('init playNextAction')
		super(playNextAction, self).__init__(config.icons['baseline-menu-open.svg'], 'Play Next', parent)
		self.focusedList = focusedList
		self.triggered.connect(self.playNextTriggered)

	def playNextTriggered(self, checked):
		addSongs(self.focusedList, self.parent(), True)


class addToPlaylistAction(QAction):
	def __init__(self, playlist, parent, focusedList):
		# print('init addToPlaylistAction')
		super(addToPlaylistAction, self).__init__(playlist['name'], parent)
		self.focusedList = focusedList
		self.playlist = playlist
		self.triggered.connect(self.addToPlaylist)

	def addToPlaylist(self):
		items = getItemsFromList(self.focusedList)
		addUs = []
		for item in items:
			if item['type'] == 'song':
				addUs.append(item)
		self.parent().signals.addSongsToPlaylist.emit(self.playlist['id'], addUs)


class addToPlaylistMenu(QMenu):
	def __init__(self, parent, focusedList):
		# print('init addToPlaylistMenu')
		super(addToPlaylistMenu, self).__init__("Add To Playlist", parent)
		self.setIcon(config.icons['baseline-playlist-add.svg'])
		self.focusedList = focusedList
		try:
			for playlist in self.parent().playlistCache:
				self.addAction(addToPlaylistAction(playlist, parent, focusedList))
		except AttributeError:
			pass


class goToAlbumAction(QAction):
	def __init__(self, parent, focusedList):
		super(QAction, self).__init__(config.icons['baseline-subdirectory-arrow-right.svg'], 'Go To Album', parent)
		self.focusedList = focusedList
		self.triggered.connect(self.goToAlbum)

	def goToAlbum(self):
		items = getItemsFromList(self.focusedList)
		if len(items) > 0:
			self.parent().signals.loadAlbumWithId.emit(items[0]['albumId'], {'display': True,
																			 'afterCurrent': False})


class removeFromQueue(QAction):
	def __init__(self, parent, focusedList):
		super(QAction, self).__init__(config.icons['baseline-remove-circle-outline.svg'], 'Remove From Queue', parent)
		self.focusedList = focusedList
		self.triggered.connect(self.removeFromQueue)

	def removeFromQueue(self):
		items = getItemsFromList(self.focusedList)
		ids = []
		if len(items) > 0:
			for item in items:
				ids.append(item['id'])
			self.parent().playbackController.removeFromQueue(ids)
