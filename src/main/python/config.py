import os

import yaml
from PyQt5.QtGui import QIcon
from fbs_runtime.application_context.PyQt5 import ApplicationContext


class configManager():
	def __init__(self):
		super(configManager, self).__init__()
		self.appContext = ApplicationContext()
		self.icons = {}
		for item in ['baseline-play-arrow.svg',
					 'baseline-pause.svg',
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

					 ]:
			self.icons[item] = self.loadIcon(item)
		try:
			with open('config.yaml') as file:
				userConfig = yaml.full_load(file)
		except FileNotFoundError:
			userConfig = {}
			print('config not found.')
		if not userConfig:
			userConfig = {}
		self.fallbackConfig = {
			'domain': 'example.com',
			'fqdn': 'https://example.com',
			'username': 'yourUsername',
			'password': 'yourPassword',
			'volume': 100,
			'appname': 'airsonic-desktop',
			'followPlaybackInQueue': True,
			'repeatList': True,  # can also be "1"
		}
		for item in self.fallbackConfig:
			if item in userConfig:
				setattr(self, item, userConfig[item])
			else:
				setattr(self, item, self.fallbackConfig[item])

	def save(self):
		saveme = {}
		for item in self.fallbackConfig.keys():
			saveme[item] = getattr(self, item)
		with open('config.yaml', 'w') as file:
			file.write(yaml.safe_dump(saveme))

	def loadIcon(self, name):
		return QIcon(self.appContext.get_resource('icons' + os.path.sep + name))


config = configManager()
