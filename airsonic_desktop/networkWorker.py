from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from libsonic import Connection


class networkWorker(QObject):
	# whether the server could be connected to, and the error if any
	connectResult = pyqtSignal(bool)
	returnAlbums = pyqtSignal(object, str)
	returnAlbumSongs = pyqtSignal(object)
	returnSongHandle = pyqtSignal(object, object)

	@pyqtSlot(str, str, str, result=bool)
	def connectToServer(self, domain, username, password):
		print('connecting to {}'.format(domain))
		domain = domain.strip()
		if not domain[0:8] == "https://" and not domain[0:7] == "http://":
			domain = "https://" + domain
		self.connection = Connection(domain, username, password, port=443, appName="airsonic-desktop",
									 apiVersion="1.15.0")
		ping = self.connection.ping()
		print(ping)
		self.connectResult.emit(ping)

	@pyqtSlot(str)
	def getAlbumsOfType(self, type):
		print('getting {} albums'.format(type))
		if type == "random":
			albums = self.connection.getAlbumList2('random', 50, 0)
		self.returnAlbums.emit(albums, type)

	@pyqtSlot(int)
	def getAlbumSongs(self, id):
		print('getting songs for album {}'.format(id))
		songs = self.connection.getAlbum(id)
		self.returnAlbumSongs.emit(songs)

	@pyqtSlot(object)
	def getSongHandle(self, song):
		# TODO: set max bitrate if configured
		handle = self.connection.stream(song['id'])
		self.returnSongHandle.emit(song, handle)
