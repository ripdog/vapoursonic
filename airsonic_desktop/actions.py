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
		print('init playLastAction')
		super(playLastAction, self).__init__(QIcon('icons/baseline-playlist-add.svg'), 'Play Last', parent)
		self.list = list
		self.triggered.connect(self.playLastTriggered)

	def playLastTriggered(self, checked):
		addSongs(self.list, self.parent(), False)


class playNextAction(QAction):
	def __init__(self, parent, list):
		print('init playNextAction')
		super(playNextAction, self).__init__(QIcon('icons/baseline-menu-open.svg'), 'Play Next', parent)
		self.list = list
		self.triggered.connect(self.playNextTriggered)

	def playNextTriggered(self, checked):
		addSongs(self.list, self.parent(), True)


class addToPlaylistAction(QAction):
	def __init__(self, playlist, parent, list):
		print('init addToPlaylistAction')
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
		print('init addToPlaylistMenu')
		super(addToPlaylistMenu, self).__init__(parent)
		self.list = list
		try:
			for playlist in self.parent().playlistCache:
				self.addAction(addToPlaylistAction(playlist, parent, list))
		except AttributeError:
			pass
