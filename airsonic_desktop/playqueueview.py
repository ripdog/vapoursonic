from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeView, QMenu


class PlayQueueView(QTreeView):
	def __init__(self, parent):
		super(PlayQueueView, self).__init__(parent)
		self.playbackController = lambda: self.window().playbackController

		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(self.playQueueMenu)

	def playQueueMenu(self, position):
		if len(self.selectedIndexes()) > 0:
			menu = QMenu()
			for item in self.window().playQueueActions:
				try:
					menu.addAction(item)
				except TypeError:
					menu.addMenu(item)
			menu.exec_(self.mapToGlobal(position))

	def playSelectedSongFromQueue(self):
		print('playing song from queue')
		indexes = self.selectedIndexes()
		if len(indexes) > 0:
			self.window().playbackController.playSongFromQueue(indexes[0])
