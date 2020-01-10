from urllib.error import URLError

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
from libsonic import Connection, AuthError, CredentialError, VersionError, ParameterError, SonicError, LicenseError, \
	DataNotFoundError

from re import sub
from vapoursonic_pkg.config import config

errors = (SonicError,
		  ParameterError,
		  VersionError,
		  VersionError,
		  CredentialError,
		  AuthError,
		  LicenseError,
		  DataNotFoundError,
		  URLError)


class networkWorker(QObject):
	connectResult = pyqtSignal(bool)
	returnAlbums = pyqtSignal(object, str)
	returnAlbumSongs = pyqtSignal(object, object)
	returnSongHandle = pyqtSignal(object, object)
	returnAlbumArtHandle = pyqtSignal(object, str, str)
	returnPlaylists = pyqtSignal(object)
	returnPlaylistSongs = pyqtSignal(object, object)
	returnSearchResults = pyqtSignal(object, int)
	returnArtistAlbums = pyqtSignal(object, object)
	returnArtists = pyqtSignal(object)
	returnMusicFolder = pyqtSignal(object, str)
	returnRootMusicFolders = pyqtSignal(object)
	errorHandler = pyqtSignal(str)
	showMessageBox = pyqtSignal(str)

	def handleErr(self, e):
		if hasattr(e, 'reason'):
			e = e.reason
		self.errorHandler.emit(str(e))

	@pyqtSlot(bool, result=bool)
	def connectToServer(self, _):
		try:
			print('connecting to {}'.format(config.domain))
			domain = config.domain.strip()
			domain = sub(r'https?://', '', domain)
			domain = sub(r'/', '', domain)
			if config.useTLS:
				scheme = "https"
			else:
				scheme = 'http'
			if config.customPort:
				port = config.customPort
			else:
				if config.useTLS:
					port = 443
				else:
					port = 80
			noportdomain = f"{scheme}://{domain}"
			config.fqdn =  f"{scheme}://{domain}:{port}"
			print(f'fqdn: {config.fqdn}')
			self.connection = Connection(noportdomain, config.username, config.password, port=port, appName=config.appname,
										 apiVersion="1.15.0")
			ping = self.connection.ping()
			print(ping)
			self.connectResult.emit(ping)
		except errors as e:
			self.handleErr(e)

	@pyqtSlot(str, int)
	def getDataForAlbumTreeView(self, type, page=0):
		try:
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
		except errors as e:
			self.handleErr(e)

	@pyqtSlot(str)
	def loadMusicFolder(self, folderId):
		try:
			folders = self.connection.getMusicDirectory(folderId)
			if 'directory' in folders:
				for item in folders['directory']['child']:
					item['type'] = 'musicFolder'
			self.returnMusicFolder.emit(folders, folderId)
		except errors as e:
			self.handleErr(e)

	@pyqtSlot()
	def loadRootMusicFolders(self):
		try:
			folders = self.connection.getMusicFolders()
			if 'musicFolders' in folders and 'musicFolder' in folders['musicFolders']:
				for item in folders['musicFolders']['musicFolder']:
					item['type'] = 'rootMusicFolder'
			self.returnRootMusicFolders.emit(folders)
		except errors as e:
			self.handleErr(e)

	@pyqtSlot(str, object)
	def loadAlbumWithId(self, id, addToQueue):
		try:
			print('getting songs for album {}'.format(id))
			songs = self.connection.getAlbum(id)
			for item in songs['album']['song']:
				item['type'] = 'song'
			songs = songs['album']
			songs['type'] = 'album'
			self.returnAlbumSongs.emit(songs, addToQueue)
		except errors as e:
			self.handleErr(e)

	@pyqtSlot()
	def getPlaylists(self):
		try:
			ret = self.connection.getPlaylists()
			if ret and ret['status'] == 'ok':
				for item in ret['playlists']['playlist']:
					item['type'] = 'playlist'
			self.returnPlaylists.emit(ret)
		except errors as e:
			self.handleErr(e)

	@pyqtSlot(str, object)
	def getPlaylistSongs(self, id, addToQueue):
		try:
			ret = self.connection.getPlaylist(id)
			ret['type'] = 'playlist'
			for item in ret['playlist']['entry']:
				item['type'] = 'song'
			self.returnPlaylistSongs.emit(ret, addToQueue)
		except errors as e:
			self.handleErr(e)

	@pyqtSlot(str, object)
	def addSongsToNewPlaylist(self, name, songs):
		try:
			ids = []
			for song in songs:
				ids.append(song['id'])
			self.connection.createPlaylist(name=name, songIds=ids)
			self.showMessageBox.emit('Created playlist {} with {} songs'.format(name, len(ids)))
			self.getPlaylists()
		except errors as e:
			self.handleErr(e)

	@pyqtSlot(str, object)
	def addSongsToPlaylist(self, id, songs):
		try:
			songlist = []
			for song in songs:
				songlist.append(song['id'])
			self.connection.updatePlaylist(id, songIdsToAdd=songlist)
			self.showMessageBox.emit('Added {} songs to playlist'.format(len(songlist)))
		except errors as e:
			self.handleErr(e)

	@pyqtSlot(str, int)
	def beginSearch(self, query, page=0):
		try:
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
		except errors as e:
			self.handleErr(e)

	@pyqtSlot(str, object)
	def loadAlbumsForArtist(self, id, index):
		try:
			ret = self.connection.getArtist(id)
			if ret and ret['artist'] and ret['artist']['album']:
				for item in ret['artist']['album']:
					item['type'] = 'album'
			self.returnArtistAlbums.emit(ret, index)
		except errors as e:
			self.handleErr(e)
