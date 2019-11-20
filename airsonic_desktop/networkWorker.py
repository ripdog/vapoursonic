from PySide2.QtCore import QObject, Slot, Signal
from libsonic import Connection


class networkWorker(QObject):
	# whether the server could be connected to, and the error if any
	connectResult = Signal(bool)

	@Slot(str, str, str)
	def connectToServer(self, domain, username, password):
		print(domain)
		print('connecting')
		domain = domain.strip()
		if not domain[0:8] == "https://" or not domain[0:7] == "http://":
			domain = "https://" + domain
		self.connection = Connection(domain, username, password, port=443, appName="airsonic-desktop",
									 apiVersion="1.15.0")
		ping = self.connection.ping()
		self.connectResult.emit(ping)

	@Slot()
	def loadRandomAlbums(self):
		print('getting random albums')
		albums = self.connection.getAlbumList2('random', 50, 0)
