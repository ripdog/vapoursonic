from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QItemSelectionModel
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QTreeView, QMenu, QHeaderView, QAbstractItemView


class PlayQueueView(QTreeView):
	def __init__(self, parent):
		super(PlayQueueView, self).__init__(parent)
		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(self.playQueueMenu)
		self.setIndentation(0)
		self.setAlternatingRowColors(True)
		self.setEditTriggers(QAbstractItemView.NoEditTriggers) # no editing possible
		self.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.setSelectionBehavior(QAbstractItemView.SelectRows)

	def showEvent(self, a0: QtGui.QShowEvent) -> None:
		super(PlayQueueView, self).showEvent(a0)
		self.header().setSectionResizeMode(QHeaderView.ResizeToContents)
		self.setColumnWidth(0, 25)
		self.setColumnWidth(1, 25)

	# self.header().setSectionResizeMode(0, QHeaderView.Fixed)
	# self.header().setSectionResizeMode(1, QHeaderView.Fixed)

	def moveSongs(self, direction):
		# direction is True for up and False for down
		selectme = []
		moveitems = []
		topMoveFence = 0
		# this is used to stop songs being moved to the top of the list and changing order
		for index in reversed(self.selectedIndexes()):
			if index.column() == 0:
				moveitems.append((self.model().takeRow(index.row()), index.row()))
		moveitems.sort(key=lambda item: item[1])
		for data in moveitems:
			item = data[0]
			index = data[1]
			if direction:
				insertPoint = index - 1
			else:
				insertPoint = index + 1
			if insertPoint <= topMoveFence:
				insertPoint = topMoveFence
				topMoveFence += 1
			if insertPoint > self.model().rowCount():
				insertPoint = self.model().rowCount()
			self.model().insertRow(insertPoint, item)
			selectme.append(insertPoint)
		self.selectionModel().clear()
		for item in selectme:
			index = self.model().index(item, 0)
			self.selectionModel().select(index, QItemSelectionModel.Rows |
										 QItemSelectionModel.Select)
		self.window().playbackController.syncMpvPlaylist()

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
			for item in self.actionsObjects:
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
