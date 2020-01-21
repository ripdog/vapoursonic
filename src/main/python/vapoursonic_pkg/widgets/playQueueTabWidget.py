from PyQt5.QtCore import QSize, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabBar, QHBoxLayout, QPushButton, QStackedWidget

from vapoursonic_pkg import vapoursonicActions
from vapoursonic_pkg.config import config
from vapoursonic_pkg.playQueueModel import playQueueModel
from vapoursonic_pkg.widgets.playqueueview import PlayQueueView


class playQueueTabWidget(QWidget):
	viewChanged = pyqtSignal(PlayQueueView)
	def __init__(self, parent):
		super(playQueueTabWidget, self).__init__(parent)

		self.playQueueViews = []
		self.currentlyPlayingTab = 0

		self.mainLayout = QVBoxLayout()
		self.mainLayout.setContentsMargins(0,0,0,0)
		self.tabBar = QTabBar(self)
		self.tabBar.setExpanding(False)
		self.tabBar.currentChanged.connect(self.displayQueueByIndex)
		self.tabBarLayout = QHBoxLayout()
		self.tabBarLayout.setContentsMargins(0,0,3,0)
		self.tabBarLayout.addWidget(self.tabBar)
		self.newTabButton = QPushButton(self)
		self.newTabButton.setIcon(config.icons['baseline-add.svg'])
		self.newTabButton.setToolTip('Open a new play queue.')
		size = self.tabBar.geometry().height()
		self.newTabButton.setFixedSize(QSize(size, size))
		self.newTabButton.clicked.connect(self.createPlayQueue)
		self.tabBarLayout.addWidget(self.newTabButton)
		self.mainLayout.addLayout(self.tabBarLayout)
		self.stackWidget = QStackedWidget(self)
		self.mainLayout.addWidget(self.stackWidget)
		self.setLayout(self.mainLayout)

	def displayQueueByIndex(self, index):
		self.stackWidget.setCurrentIndex(index)
		self.viewChanged.emit(self.playQueueViews[index][0])

	def queueDoubleClicked(self, index):
		self.window().playbackController.playSongFromQueue(index, self.playQueueViews[self.tabBar.currentIndex()][1])

	def createPlayQueue(self):
		parentView = QWidget()
		layout = QHBoxLayout(parentView)
		view = PlayQueueView(parentView)
		layout.addWidget(view)
		layout.setContentsMargins(0, 0, 0, 0)
		model = playQueueModel(self)
		view.setModel(model)
		view.doubleClicked.connect(self.queueDoubleClicked)
		self.attachActionsForQueue(view)
		self.playQueueViews.append((view, model))
		index = self.tabBar.addTab(f'Queue &{self.tabBar.count() + 1}')
		widgetIndex = self.stackWidget.addWidget(parentView)
		assert index == widgetIndex
		self.tabBar.setCurrentIndex(index)
		if index == self.currentlyPlayingTab:
			self.tabBar.setTabIcon(index, config.icons['baseline-play-arrow.svg'])
		return view, model

	def attachActionsForQueue(self, view):
		view.actionsObjects = [vapoursonicActions.goToAlbumAction(self.window(), view),
								 vapoursonicActions.removeFromQueue(self.window(), view),
								 vapoursonicActions.addToPlaylistMenu(self.window(), view),
								 vapoursonicActions.copyDetailsMenu(self.window(), view)]

	def currentPlayingModelChanged(self, model):
		self.tabBar.setTabIcon(self.currentlyPlayingTab, QIcon())
		for i in range(0, len(self.playQueueViews)):
			if self.playQueueViews[i][1] == model:
				self.currentlyPlayingTab = i
				self.tabBar.setTabIcon(i, config.icons['baseline-play-arrow.svg'])