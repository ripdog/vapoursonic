from PyQt5.QtGui import QStandardItemModel, QStandardItem


class playQueueModel(QStandardItemModel):
	def __init__(self, controller):
		super(playQueueModel, self).__init__()
		self.controller = controller
		self.headerMapping = {
			'': None,
			'Track No.': 'track',
			'Title': 'title',
			'Album': 'album',
			'Artist': 'artist'
		}

		self.refreshHeaderLabels()

	def refreshHeaderLabels(self):
		self.setHorizontalHeaderLabels(list(self.headerMapping))


	# commented because drag and drop doesnt work well
	# def dropMimeData(self, data, action, row, col, parent):
	# 	"""
	# 	Always move the entire row, and don't allow column "shifting"
	# 	"""
	# 	currentSongId = self.controller.currentSong.data()['id']
	# 	self.controller.currentSong = None
	# 	ret = super().dropMimeData(data, action, row, 0, parent)
	# 	self.controller.setCurrentSongFromId(currentSongId)
	# 	self.controller.syncMpvPlaylist()
	# 	return ret

	def addSongs(self, songs, playThisSongNow=None, afterRow=None):
		currentSongStandardObject = None
		for item in songs:
			standardItems = []
			for key in self.headerMapping.values():
				if not key:
					standardItems.append(songItem('', item))
					continue
				try:
					standardItems.append(songItem(str(item[key]), item))
				except KeyError:
					standardItems.append(songItem('No {}'.format(key), item))
			if afterRow:
				self.insertRow(afterRow, standardItems)
				afterRow += 1
				print('inserting row for {}'.format(item['title']))
			else:
				self.appendRow(standardItems)
			if playThisSongNow and playThisSongNow['id'] == item['id']:
				currentSongStandardObject = standardItems[0]
		if currentSongStandardObject:
			return currentSongStandardObject

class songItem(QStandardItem):
	def __init__(self, string, data):
		super(songItem, self).__init__(string)
		assert data['type'] == 'song'
		self.setData(data)
		self.setDropEnabled(False)
