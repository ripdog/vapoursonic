import yaml

config = {'domain': 'example.com', 'username': 'yourUsername',
		  'password': 'yourPassword', 'volume': 100, 'cacheLocation': 'cache'}
try:
	with open('config.yaml') as file:
		config = yaml.full_load(file)
except:
	print('loading config failed. Using default.')
