from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from libsonic import Connection

from config import config


class networkWorker(QObject):
	# whether the server could be connected to, and the error if any
	connectResult = pyqtSignal(bool)
	returnAlbums = pyqtSignal(object, str)
	returnAlbumSongs = pyqtSignal(object, object)
	returnSongHandle = pyqtSignal(object, object)
	returnAlbumArtHandle = pyqtSignal(object, str)
	returnPlaylists = pyqtSignal(object)
	returnPlaylistSongs = pyqtSignal(object, object)
	returnSearchResults = pyqtSignal(object, int)
	returnArtistAlbums = pyqtSignal(object, object)
	returnArtists = pyqtSignal(object)

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

	@pyqtSlot(str, int)
	def getDataForAlbumTreeView(self, type, page=0):
		print('getting {} data'.format(type))
		if type not in ['random', 'newest', 'recent', 'frequent', 'alphabeticalByName', 'artists']:
			raise ValueError('Incorrect data type requested')
		if type == 'artists':
			artists = self.connection.getArtists()
			for index in artists['artists']['index']:
				for artist in index['artist']:
					artist['type'] = 'artist'
			self.returnArtists.emit(artists)
		else:
			albums = self.connection.getAlbumList2(type, 50, page * 50)
			for item in albums['albumList2']['album']:
				item['type'] = 'album'
			self.returnAlbums.emit(albums, type)

	@pyqtSlot(str, object)
	def loadAlbumWithId(self, id, addToQueue):
		print('getting songs for album {}'.format(id))
		songs = self.connection.getAlbum(id)
		for item in songs['album']['song']:
			item['type'] = 'song'
		songs = songs['album']
		songs['type'] = 'album'
		self.returnAlbumSongs.emit(songs, addToQueue)

	@pyqtSlot(str)
	def getAlbumArtWithId(self, id):
		self.returnAlbumArtHandle.emit(self.connection.getCoverArt(id, 128), id)

	@pyqtSlot()
	def getPlaylists(self):
		ret = self.connection.getPlaylists()
		if ret and ret['status'] == 'ok':
			for item in ret['playlists']['playlist']:
				item['type'] = 'playlist'
		self.returnPlaylists.emit(ret)

	@pyqtSlot(str, object)
	def getPlaylistSongs(self, id, addToQueue):
		ret = self.connection.getPlaylist(id)
		ret['type'] = 'playlist'
		for item in ret['playlist']['entry']:
			item['type'] = 'song'
		self.returnPlaylistSongs.emit(ret, addToQueue)

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
