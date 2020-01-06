from datetime import timedelta

from PyQt5.QtCore import pyqtSignal, QPoint
from PyQt5.QtWidgets import QSlider, QApplication, QStyleOptionSlider, QToolTip, QLabel, QStyle


class trackProgressSlider(QSlider):
	def __init__(self, *args):
		super(trackProgressSlider, self).__init__(*args)
		self.sliderPressed.connect(self.trackSliderPressed)
		self.sliderReleased.connect(self.trackSliderReleased)
		self.sliderMoved.connect(self.displaySliderMoveTimeIndicator)
		self.sliderBeingDragged = False
		self.style = QApplication.style()
		self.opt = QStyleOptionSlider()
		self.label = QLabel(self.parent())
		self.label.setStyleSheet("background-color: #343434; "
								 "color: #ECECEC;"
								 "margin: 3px;")
		self.label.hide()

	def progressUpdate(self, value, total):
		if not self.sliderBeingDragged:
			self.blockSignals(True)
			self.setValue(value)
			self.setRange(0, total)
			self.blockSignals(False)

	def trackSliderPressed(self):
		self.sliderBeingDragged = True
		self.label.show()

	def trackSliderReleased(self):
		self.sliderBeingDragged = False
		self.label.hide()

	def displaySliderMoveTimeIndicator(self, value):
		self.initStyleOption(self.opt)
		rectHandle = self.style.subControlRect(self.style.CC_Slider, self.opt, self.style.SC_SliderHandle)
		val = str(timedelta(seconds=value))
		labelWidth = self.label.fontMetrics().width(val) + 13
		posLocal = rectHandle.center() + QPoint(-(labelWidth / 2), -55)
		convertedToWindow = self.parent().mapFromGlobal(self.mapToGlobal(posLocal))
		self.label.setMaximumWidth(labelWidth)
		self.label.setText(val)
		self.label.move(convertedToWindow)
