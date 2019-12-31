from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QToolButton, QStyle


class toastMessageDisplay(QWidget):
	def __init__(self, *args):
		super(toastMessageDisplay, self).__init__(*args)
		self.priorityMessage = None
		self.hideTimer = QTimer()
		self.hideTimer.setSingleShot(True)
		self.hideTimer.timeout.connect(self.hide)
		self.hide()
		#setup contents
		self.centerLayout = QHBoxLayout(self)
		self.notificationLabel = QLabel(self)
		self.closeButton = QToolButton(self)
		self.centerLayout.addWidget(self.notificationLabel)
		self.centerLayout.addWidget(self.closeButton)

		self.setFixedSize(500,50)
		self.parent().signals.resized.connect(self.setPosition)
		self.setPosition()
		self.setStyleSheet("background-color: #343434;"
						   "color: #ECECEC;"
						   "margin: 3px;")
		self.closeButton.setIcon(self.parent().style().standardIcon(QStyle.SP_DialogCloseButton))
		self.closeButton.setStyleSheet("background: transparent;")
		self.closeButton.clicked.connect(self.hide)

	def setPosition(self):
		y = round(self.parent().size().height() * 0.7)
		x = round(self.parent().size().width() * 0.5)
		self
		self.move(x,y)

	def showMessage(self, message):
		self.notificationLabel.setText(message)
		self.show()
		self.hideTimer.start(5000)