from PyQt5.QtCore import QRegExp, Qt
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from fbs_runtime.application_context.PyQt5 import ApplicationContext

from vapoursonic.config import config

def setAutoConnectState(state):
	if state == 0:
		config.autoConnect = False
	else:
		config.autoConnect = True

class settingsDialog(QDialog):
	def __init__(self):
		appcontext = ApplicationContext()
		super(settingsDialog, self).__init__()
		uic.loadUi(appcontext.get_resource('settings.ui'), self)
		self.autoConnectCheckBox.setChecked(config.autoConnect)
		self.applicationNameLineEdit.setText(config.appname)
		if not config.streamTypeDownload:
			self.streamTypeStreamRadioButton.setChecked(True)
		else:
			self.streamTypeDownloadRadioButton.setChecked(True)
		#connect signals
		self.autoConnectCheckBox.stateChanged.connect(setAutoConnectState)
		self.applicationNameLineEdit.editingFinished.connect(self.setAppName)
		regexValidator = QRegExpValidator(QRegExp(r'.{3,}'))  # require at least 3
															# letters in the app name
		self.applicationNameLineEdit.setValidator(regexValidator)
		self.streamTypeStreamRadioButton.toggled.connect(self.streamTypeChanged)

		self.setModal(True)
		self.tabWidget.setCurrentIndex(0)
		self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
		self.exec_()

	def setAppName(self):
		print('setting AppName')
		config.appname = self.applicationNameLineEdit.text()

	def streamTypeChanged(self):
		if self.streamTypeStreamRadioButton.isChecked():
			config.streamTypeDownload = False
		else:
			config.streamTypeDownload = True
