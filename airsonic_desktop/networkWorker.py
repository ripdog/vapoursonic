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
	returnPlaylists = pyqtSignal(object)
	returnPlaylistSongs = pyqtSignal(object)
	returnSearchResults = pyqtSignal(object, int)
	returnArtistAlbums = pyqtSignal(object, object)

	@pyqtSlot(str, str, str, result=bool)
	def connectToServer(self, domain, username, password):
		print('connecting to {}'.format(domain))
		domain = domain.strip()
		if not domain[0:8] == "https://" and not domain[0:7] == "http://":
			domain = "https://" + domain
		config.fqdn = domain
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
		else:
			raise AttributeError('Incorrect album type requested')
		for item in albums['albumList2']['album']:
			item['type'] = 'album'
		self.returnAlbums.emit(albums, type)

	@pyqtSlot(int)
	def getAlbumSongs(self, id):
		print('getting songs for album {}'.format(id))
		songs = self.connection.getAlbum(id)
		for item in songs['album']['song']:
			item['type'] = 'song'
		self.returnAlbumSongs.emit(songs)

	@pyqtSlot(str)
	def getAlbumArtWithId(self, id):
		self.returnAlbumArtHandle.emit(self.connection.getCoverArt(id, 128), id)

	@pyqtSlot()
	def getPlaylists(self):
		self.returnPlaylists.emit(self.connection.getPlaylists())

	@pyqtSlot(str)
	def getPlaylistSongs(self, id):
		ret = self.connection.getPlaylist(id)
		ret['type'] = 'playlist'
		self.returnPlaylistSongs.emit(self.connection.getPlaylist(id))

	@pyqtSlot(str, object)
	def addSongsToPlaylist(self, id, songs):
		songlist = []
		for song in songs:
			songlist.append(song['id'])
		self.connection.updatePlaylist(id, songIdsToAdd=songlist)

	@pyqtSlot(str, int)
	def beginSearch(self, query, page=0):
		ret = self.connection.search3(query, artistOffset=page * 20, albumOffset=page * 20, songOffset=page * 20)
		if 'album' in ret['searchResult3']:
			for item in ret['searchResult3']['album']:
				item['type'] = 'album'
		if 'artist' in ret['searchResult3']:
			for item in ret['searchResult3']['artist']:
				item['type'] = 'artist'
		if 'song' in ret['searchResult3']:
			for item in ret['searchResult3']['song']:
				item['type'] = 'song'
		self.returnSearchResults.emit(ret['searchResult3'], page)

	@pyqtSlot(str, object)
	def loadAlbumsForArtist(self, id, index):
		ret = self.connection.getArtist(id)
		if ret and ret['artist'] and ret['artist']['album']:
			for item in ret['artist']['album']:
				item['type'] = 'album'
		self.returnArtistAlbums.emit(ret, index)
