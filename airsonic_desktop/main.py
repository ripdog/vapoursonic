from PySide2.QtCore import QThread, Slot, QModelIndex, Signal
from PySide2.QtGui import QStandardItemModel, QStandardItem
from PySide2.QtWidgets import QApplication, QMainWindow

import config
from networkWorker import networkWorker
from ui_mainwindow import Ui_AirsonicDesktop


class MainWindow(QMainWindow):
	loadRandomAlbums = Signal()

	def __init__(self, *args, **kwargs):
		super(MainWindow, self).__init__(*args, **kwargs)
		self.networkThread = QThread()
		self.networkWorker = networkWorker()
		self.networkWorker.moveToThread(self.networkThread)
		self.ui = Ui_AirsonicDesktop()
		self.ui.setupUi(self)

		self.populateConnectFields()

		self.ui.stackedWidget.setCurrentIndex(0)

		self.ui.connectButton.clicked.connect(lambda: self.networkWorker.connectToServer(
			self.ui.domainInput.text(),
			self.ui.usernameInput.text(),
			self.ui.passwordInput.text()
		))
		self.networkWorker.connectResult.connect(self.connectResult)
		self.loadRandomAlbums.connect(self.networkWorker.loadRandomAlbums)

	def populateConnectFields(self):
		self.ui.domainInput.setText(config.config['domain'])
		self.ui.usernameInput.setText(config.config['username'])
		self.ui.passwordInput.setText(config.config['password'])

	@Slot()
	def connectResult(self, success):
		if success:
			self.ui.stackedWidget.setCurrentIndex(1)
			self.populateAlbumList()
		else:
			pass

	# should slap an error somewhere lol

	def populateAlbumList(self):
		items = []
		self.albumListModel = QStandardItemModel()
		for item in ['Playlists', 'Random', 'Recently Added', 'Artists', 'Albums', 'Folders']:
			standardItem = QStandardItem(item)
			if not item == "Random":
				standardItem.appendRow(QStandardItem('Loading...'))
			self.albumListModel.appendRow(standardItem)
		self.ui.albumTreeList.setModel(self.albumListModel)
		self.ui.albumTreeList.setHeaderHidden(True)
		self.ui.albumTreeList.clicked[QModelIndex].connect(self.albumListClick)

	def albumListClick(self, index):
		item = self.albumListModel.itemFromIndex(index)
		text = item.text()
		if text == "Loading...":
			pass
		elif text == "Random":


if __name__ == "__main__":
	app = QApplication([])
	window = MainWindow()
	window.show()
	app.exec_()
