import yaml


class configManager():
	def __init__(self):
		super(configManager, self).__init__()
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
			'appname': 'airsonic-desktop'
		}
		for item in self.fallbackConfig:
			if item in userConfig:
				setattr(self, item, userConfig[item])
			else:
				setattr(self, item, self.fallbackConfig[item])

	def save(self):
		saveme = {}
		for item in dir(self):
			if not item.startswith('_') and item in self.fallbackConfig.keys():
				saveme[item] = getattr(self, item)
		with open('config.yaml', 'w') as file:
			file.write(yaml.safe_dump(saveme))


config = configManager()
