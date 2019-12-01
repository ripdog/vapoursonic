from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from libsonic import Connection

from config import config


class networkWorker(QObject):
	# whether the server could be connected to, and the error if any
	connectResult = pyqtSignal(bool)
	returnAlbums = pyqtSignal(object, str)
	returnAlbumSongs = pyqtSignal(object)
	returnSongHandle = pyqtSignal(object, object)
	returnAlbumArtHandle = pyqtSignal(object, str)

	@pyqtSlot(str, str, str, result=bool)
	def connectToServer(self, domain, username, password):
		print('connecting to {}'.format(domain))
		domain = domain.strip()
		if not domain[0:8] == "https://" and not domain[0:7] == "http://":
			domain = "https://" + domain
		config['fqdn'] = domain
		self.connection = Connection(domain, username, password, port=443, appName="airsonic-desktop",
									 apiVersion="1.15.0")
		ping = self.connection.ping()
		print(ping)
		self.connectResult.emit(ping)

	@pyqtSlot(str)
	def getAlbumsOfType(self, type, page=0):
		print('getting {} albums'.format(type))
		if type == "random":
			albums = self.connection.getAlbumList2('random', 50, page)
		elif type == 'recentlyAdded':
			albums = self.connection.getAlbumList2('newest', 50, page)
		elif type == 'recentlyPlayed':
			albums = self.connection.getAlbumList2('recent', 50, page)
		elif type == 'albums':
			albums = self.connection.getAlbumList2('alphabeticalByName', 50, page)
		self.returnAlbums.emit(albums, type)

	@pyqtSlot(int)
	def getAlbumSongs(self, id):
		print('getting songs for album {}'.format(id))
		songs = self.connection.getAlbum(id)
		self.returnAlbumSongs.emit(songs)

	def getSongHandle(self, song):
		# TODO: set max bitrate if configured
		handle = self.connection.download(song['id'])
		self.returnSongHandle.emit(song, handle)

	# test urls: https://***REMOVED***/rest/download.view?f=json&v=1.15.0&c=airsonic-desktop&u=ripdog&s=bce396f3e7a0&t=4d0ad881fb5a66b0867af131eef68bf2&id=444
	# https://***REMOVED***/rest/download.view?f=json&v=1.15.0&c=airsonic-desktop&u=ripdog&s=bce396f3e7a0&t=4d0ad881fb5a66b0867af131eef68bf2&id=437
	# player.playlist_append('https://***REMOVED***/rest/download.view?f=json&v=1.15.0&c=airsonic-desktop&u=ripdog&s=bce396f3e7a0&t=4d0ad881fb5a66b0867af131eef68bf2&id=7217')
	# player.playlist_append('https://***REMOVED***/rest/download.view?f=json&v=1.15.0&c=airsonic-desktop&u=ripdog&s=bce396f3e7a0&t=4d0ad881fb5a66b0867af131eef68bf2&id=7221')
	@pyqtSlot(str)
	def getAlbumArtWithId(self, id):
		self.returnAlbumArtHandle.emit(self.connection.getCoverArt(id, 128), id)
