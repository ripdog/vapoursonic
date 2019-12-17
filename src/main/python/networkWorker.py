import functools
from urllib.error import URLError

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from libsonic import Connection, CredentialError

from config import config


class networkWorker(QObject):
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
	errorHandler = pyqtSignal(str)

	def catchErr(self, *exceptions):
		def decorator(func):
			@functools.wraps(func)
			def wrapper(*args, **kwargs):
				try:
					return func(*args, **kwargs)
				except exceptions or Exception as e:
					return self.handleErr(func, e)

			return wrapper

		return decorator

	def handleErr(self, func, e):
		if hasattr(e, 'reason'):
			e = e.reason
		self.errorHandler.emit(str(e))

	@catchErr(CredentialError)
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

	@catchErr(URLError)
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

	@catchErr(URLError)
	@pyqtSlot(str, object)
	def loadAlbumWithId(self, id, addToQueue):
		print('getting songs for album {}'.format(id))
		songs = self.connection.getAlbum(id)
		for item in songs['album']['song']:
			item['type'] = 'song'
		songs = songs['album']
		songs['type'] = 'album'
		self.returnAlbumSongs.emit(songs, addToQueue)

	@catchErr(URLError)
	@pyqtSlot(str)
	def getAlbumArtWithId(self, id):
		self.returnAlbumArtHandle.emit(self.connection.getCoverArt(id, 128), id)

	@catchErr(URLError)
	@pyqtSlot()
	def getPlaylists(self):
		ret = self.connection.getPlaylists()
		if ret and ret['status'] == 'ok':
			for item in ret['playlists']['playlist']:
				item['type'] = 'playlist'
		self.returnPlaylists.emit(ret)

	@catchErr(URLError)
	@pyqtSlot(str, object)
	def getPlaylistSongs(self, id, addToQueue):
		ret = self.connection.getPlaylist(id)
		ret['type'] = 'playlist'
		for item in ret['playlist']['entry']:
			item['type'] = 'song'
		self.returnPlaylistSongs.emit(ret, addToQueue)

	@catchErr(URLError)
	@pyqtSlot(str, object)
	def addSongsToPlaylist(self, id, songs):
		songlist = []
		for song in songs:
			songlist.append(song['id'])
		self.connection.updatePlaylist(id, songIdsToAdd=songlist)

	@catchErr(URLError)
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

	@catchErr(URLError)
	@pyqtSlot(str, object)
	def loadAlbumsForArtist(self, id, index):
		ret = self.connection.getArtist(id)
		if ret and ret['artist'] and ret['artist']['album']:
			for item in ret['artist']['album']:
				item['type'] = 'album'
		self.returnArtistAlbums.emit(ret, index)
