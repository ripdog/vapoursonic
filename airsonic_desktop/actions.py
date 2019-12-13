from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMenu


def getItemsFromList(list):
	items = []
	selectedItems = list.selectedIndexes()
	for item in selectedItems:
		if item.column() == 0:
			items.append(list.model().itemFromIndex(item).data())
	return items


def addSongs(list, parent, afterCurrent):
	items = getItemsFromList(list)
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
	def __init__(self, parent, list):
		# print('init playLastAction')
		super(playLastAction, self).__init__(QIcon('icons/baseline-queue.svg'), 'Add to Queue', parent)
		self.list = list
		self.triggered.connect(self.playLastTriggered)

	def playLastTriggered(self, checked):
		addSongs(self.list, self.parent(), False)


class playNextAction(QAction):
	def __init__(self, parent, list):
		# print('init playNextAction')
		super(playNextAction, self).__init__(QIcon('icons/baseline-menu-open.svg'), 'Play Next', parent)
		self.list = list
		self.triggered.connect(self.playNextTriggered)

	def playNextTriggered(self, checked):
		addSongs(self.list, self.parent(), True)


class addToPlaylistAction(QAction):
	def __init__(self, playlist, parent, list):
		# print('init addToPlaylistAction')
		super(addToPlaylistAction, self).__init__(playlist['name'], parent)
		self.list = list
		self.playlist = playlist
		self.triggered.connect(self.addToPlaylist)

	def addToPlaylist(self):
		items = getItemsFromList(self.list)
		for item in items:
			if item['type'] == 'song':
				self.parent().signals.addSongsToPlaylist.emit(self.playlist['id'], items)


class addToPlaylistMenu(QMenu):
	def __init__(self, parent, list):
		# print('init addToPlaylistMenu')
		super(addToPlaylistMenu, self).__init__("Add To Playlist", parent)
		self.setIcon(QIcon('icons/baseline-playlist-add.svg'))
		self.list = list
		try:
			for playlist in self.parent().playlistCache:
				self.addAction(addToPlaylistAction(playlist, parent, list))
		except AttributeError:
			pass


class goToAlbumAction(QAction):
	def __init__(self, parent, list):
		super(QAction, self).__init__(QIcon('icons/baseline-subdirectory-arrow-right.svg'), 'Go To Album', parent)
		self.list = list
		self.triggered.connect(self.goToAlbum)

	def goToAlbum(self):
		items = getItemsFromList(self.list)
		if len(items) > 0:
			self.parent().signals.loadAlbumWithId.emit(items[0]['albumId'], {'display': True,
																			 'afterCurrent': False})


class removeFromQueue(QAction):
	def __init__(self, parent, list):
		super(QAction, self).__init__(QIcon('icons/baseline-remove-circle-outline.svg'), 'Remove From Queue', parent)
		self.list = list
		self.triggered.connect(self.removeFromQueue)

	def removeFromQueue(self):
		items = getItemsFromList(self.list)
		ids = []
		if len(items) > 0:
			for item in items:
				ids.append(item['id'])
			self.parent().playbackController.removeFromQueue(ids)
