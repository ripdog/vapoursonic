from PyQt5 import uic, Qt
from PyQt5.Qt import PYQT_VERSION_STR
from PyQt5.QtCore import QT_VERSION_STR
from PyQt5.QtWidgets import QDialog
from fbs_runtime.application_context.PyQt5 import ApplicationContext


class aboutDialog(QDialog):
	def __init__(self):
		appcontext = ApplicationContext()
		super(aboutDialog, self).__init__()
		uic.loadUi(appcontext.get_resource('about.ui'), self)
		logoPixmap = appcontext.app_icon.pixmap(1024, 1024)
		self.logoLabel.setPixmap(logoPixmap)
		# self.logoLabel.setSize(QSize(1024,1024))
		self.versionLabel.setText(
			f'vapoursonic version: {appcontext.build_settings["version"]}, Qt version: {PYQT_VERSION_STR}, PyQt version: {QT_VERSION_STR}')
		self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
