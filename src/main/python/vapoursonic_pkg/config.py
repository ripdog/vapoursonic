import os
import pathlib
import re
import sys

import yaml
from PyQt5.QtGui import QIcon
from fbs_runtime.application_context.PyQt5 import ApplicationContext


def getPath(filename):
	if sys.platform == 'win32':
		path = os.path.expandvars(r'%APPDATA%\vapoursonic\{}'.format(filename))
	elif sys.platform == 'linux':
		path = os.path.expanduser(r'~/.config/vapoursonic/{}'.format(filename))
	else:
		print('unsupported OS!')
		path = os.path.abspath(filename)
	pathlib.Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
	return path


class configManager():
	def __init__(self):
		super(configManager, self).__init__()
		self.appContext = ApplicationContext()
		self.icons = {}

		for item in ['baseline-pause.svg',
					 'baseline-skip-next.svg',
					 'baseline-skip-previous.svg',
					 'baseline-stop.svg',
					 'audio-spectrum.svg',
					 'baseline-access-time.svg',
					 'sharp-date-range.svg',
					 'baseline-navigate-before.svg',
					 'baseline-navigate-next.svg',
					 'baseline-refresh.svg',
					 'baseline-arrow-back.svg',
					 'baseline-shuffle.svg',
					 'baseline-my-location.svg',
					 'baseline-volume-up.svg',
					 'baseline-repeat-one.svg',
					 'baseline-repeat.svg',
					 'baseline-play-arrow.svg',
					 'baseline-queue.svg',
					 'baseline-menu-open.svg',
					 'baseline-playlist-add.svg',
					 'baseline-subdirectory-arrow-right.svg',
					 'baseline-remove-circle-outline.svg',
					 'baseline-delete-outline.svg',
					 'baseline-close-white.svg',
					 'baseline-keyboard-arrow-up.svg',
					 'baseline-keyboard-arrow-down.svg',
					 'baseline-close.svg',
					 'baseline-add.svg',
					 ]:
			self.icons[item] = self.loadIcon(item)
		try:
			with open(getPath('config.yaml')) as file:
				userConfig = yaml.full_load(file)
		except FileNotFoundError:
			userConfig = {}
			print('config not found.')
		if not userConfig:
			userConfig = {}
		self.fallbackConfig = {
			'domain': '',  # e.g. example.com
			'fqdn': '',  # e.g. https://example.com - autofilled
			'username': '',
			'password': '',
			'volume': 100,
			'appname': 'vapoursonic',
			'followPlaybackInQueue': True,
			'repeatList': True,  # can also be "1"
			'playQueueState': [],
			# [{'currentIndex': 0,
			# 			   'queueServer': None,  # format: username@domain
			# 			   'queue': []
			# 			   }],
			'autoConnect': False,
			'streamTypeDownload': False,
			'useTLS': True,
			'useCustomPort': False,
			'customPort': 0,
			'playlistCache': [],
		}
		for item in self.fallbackConfig:
			if item in userConfig:
				setattr(self, item, userConfig[item])
			else:
				setattr(self, item, self.fallbackConfig[item])
		queueList = os.listdir(getPath(''))
		regex = re.compile(r'queue\d+.yaml')
		self.playQueueState = []
		for item in queueList:
			if regex.fullmatch(item):
				with open(getPath(item)) as file:
					queue = yaml.safe_load(file)
				self.playQueueState.append(queue)
		print(f'loaded {len(self.playQueueState)} queues')

	def setVar(self, var, val):
		if var in self.fallbackConfig.keys():
			setattr(self, var, val)
		else:
			raise AttributeError('invalid config variable name: {}'.format(var))

	def save(self, playbackController, viewModels):
		# don't save play queue twice
		self.playQueueState = None
		saveme = {}
		for item in self.fallbackConfig.keys():
			saveme[item] = getattr(self, item)
		writeme = yaml.safe_dump(saveme)
		with open(getPath('config.yaml'), 'w') as file:
			file.write(writeme)
		viewNo = 1
		for viewmodel in viewModels:
			saveme = {}
			if viewmodel[1] == playbackController.playQueueModel:
				try:
					saveme['currentIndex'] = playbackController.playQueueModel.indexFromItem(
						playbackController.currentSong).row()
				except RuntimeError:
					pass
			queue = [viewmodel[1].item(i, 0).data() for i in
					 range(0, viewmodel[1].rowCount())]
			saveme['queueServer'] = f'{config.username}@{config.domain}'
			saveme['queue'] = queue
			writeme = yaml.safe_dump(saveme)
			with open(getPath('queue{}.yaml'.format(viewNo)), 'w') as file:
				file.write(writeme)
			viewNo += 1

	def loadIcon(self, name):
		return QIcon(self.appContext.get_resource('icons' + os.path.sep + name))


config = configManager()
