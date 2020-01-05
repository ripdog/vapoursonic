from PyQt5.QtWidgets import QDialog
from PyQt5 import uic
from fbs_runtime.application_context.PyQt5 import ApplicationContext

from vapoursonic_pkg.config import config

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
		self.setModal(True)
		self.exec_()
