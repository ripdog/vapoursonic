from PyQt5.QtCore import QTimer, Qt, QRect
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QToolButton, QStyle

from vapoursonic.config import config


class toastMessageDisplay(QWidget):
	def __init__(self, *args):
		super(toastMessageDisplay, self).__init__(*args)
		self.priorityMessage = None
		self.hideTimer = QTimer()
		self.hideTimer.setSingleShot(True)
		self.hideTimer.timeout.connect(self.hideWidget)
		self.hide()
		self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
		# setup contents
		self.centerLayout = QHBoxLayout(self)
		self.notificationLabel = QLabel(self)
		self.closeButton = QToolButton(self)
		self.centerLayout.addWidget(self.notificationLabel)
		self.centerLayout.addWidget(self.closeButton)
		self.notificationLabel.setWordWrap(True)
		self.fm = self.notificationLabel.fontMetrics()
		self.parent().signals.resized.connect(self.setPosition)
		# self.setFixedSize(500, 50)
		# self.setPosition()
		self.setAttribute(Qt.WA_StyledBackground, True)  # This tells Qt to draw the
		# background for the entire widget area
		self.setStyleSheet("background-color: #797979;"
						   "color: #ECECEC;"
						   "margin: 3px;"
						   "border-radius: 5px;")
		self.closeButton.setIcon(config.icons['baseline-close-white.svg'])
		self.closeButton.setStyleSheet("background: transparent;")
		self.closeButton.clicked.connect(self.hide)

	def setPosition(self):
		if len(self.notificationLabel.text()) > 1:
			self.setFixedSize(500, 50)
			rect = self.fm.boundingRect(QRect(0, 0, 400, 50), #label should be 432 wide.
															# Using this value doesn't work...
										  Qt.TextWordWrap,
										  self.notificationLabel.text())
			self.setFixedSize(500, rect.height() + 31)
			y = round(self.parent().size().height() * 0.8)
			x = round(self.parent().size().width() * 0.5)
			x = x - (self.width() / 2)  # center the widget by moving it left by half of its width
			self.move(x, y)

	def showMessage(self, message):
		self.notificationLabel.setText(message)
		self.setPosition()
		self.show()
		self.hideTimer.start(6000)

	def hideWidget(self):
		self.notificationLabel.clear()
		self.hide()