from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QTreeView, QMenu, QHeaderView


class PlayQueueView(QTreeView):
	def __init__(self, parent):
		super(PlayQueueView, self).__init__(parent)
		self.playbackController = lambda: self.window().playbackController

		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(self.playQueueMenu)
		self.setIndentation(0)
		self.setAlternatingRowColors(True)


	def showEvent(self, a0: QtGui.QShowEvent) -> None:
		super(PlayQueueView, self).showEvent(a0)
		self.header().setSectionResizeMode(QHeaderView.ResizeToContents)
		self.setColumnWidth(0, 25)
		self.setColumnWidth(1, 25)
		# self.header().setSectionResizeMode(0, QHeaderView.Fixed)
		# self.header().setSectionResizeMode(1, QHeaderView.Fixed)

	# self.setDragEnabled(True)
	# self.setAcceptDrops(True)
	# self.viewport().setAcceptDrops(True)
	# self.setDragDropOverwriteMode(False)
	# self.setDropIndicatorShown(True)
	# self.setSelectionMode(QAbstractItemView.ExtendedSelection)
	# self.setSelectionBehavior(QAbstractItemView.SelectRows)
	# self.setDragDropMode(QAbstractItemView.InternalMove)

	# def dropEvent(self, event: QDropEvent):
	# 	ret = super(QTreeView, self).dropEvent(event)
	# 	print('dropevent run')
	# 	self.window().playbackController.syncMpvPlaylist()
	# 	return ret

	def playQueueMenu(self, position):
		if len(self.selectedIndexes()) > 0:
			menu = QMenu()
			for item in self.window().playQueueActions:
				try:
					menu.addAction(item)
				except TypeError:
					menu.addMenu(item)
			menu.exec_(QCursor.pos())

	def playSelectedSongFromQueue(self):
		print('playing song from queue')
		indexes = self.selectedIndexes()
		if len(indexes) > 0:
			self.window().playbackController.playSongFromQueue(indexes[0])
