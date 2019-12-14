import ctypes
import ctypes.wintypes

from PyQt5.QtCore import QObject, QRunnable, pyqtSignal


# thanks to https://gist.github.com/mdavey/6d40a89dbc15aefcc8cd

class GlobalHotKeys(QObject):
	"""
	Register a key using the register() method, or using the @register decorator
	Use listen() to start the message pump

	Example:

	from globalhotkeys import GlobalHotKeys

	@GlobalHotKeys.register(GlobalHotKeys.VK_F1)
	def hello_world():
		print 'Hello World'

	GlobalHotKeys.listen()
	"""

	key_mapping = []
	user32 = ctypes.windll.user32

	@classmethod
	def register(cls, vk, modifier=0, func=None):
		"""
		vk is a windows virtual key code
		 - can use ord('X') for A-Z, and 0-1 (note uppercase letter only)
		 - or win32con.VK_* constants
		 - for full list of VKs see: http://msdn.microsoft.com/en-us/library/dd375731.aspx

		modifier is a win32con.MOD_* constant

		func is the function to run.  If False then break out of the message loop
		"""

		# Called as a decorator?
		if func is None:
			def register_decorator(f):
				cls.register(vk, modifier, f)
				return f

			return register_decorator
		else:
			cls.key_mapping.append((vk, modifier, func))

	@classmethod
	def listen(cls):
		"""
		Start the message pump
		"""

		for index, (vk, modifiers, func) in enumerate(cls.key_mapping):
			if not cls.user32.RegisterHotKey(None, index, modifiers, vk):
				raise Exception('Unable to register hot key: ' + str(vk))

		try:
			msg = ctypes.wintypes.MSG()
			while cls.user32.GetMessageA(ctypes.byref(msg), None, 0, 0) != 0:
				if msg.message == 786:  # WM_HOTKEY
					(vk, modifiers, func) = cls.key_mapping[msg.wParam]
					if not func:
						break
					func()

				cls.user32.TranslateMessage(ctypes.byref(msg))
				cls.user32.DispatchMessageA(ctypes.byref(msg))

		finally:
			for index, (vk, modifiers, func) in enumerate(cls.key_mapping):
				cls.user32.UnregisterHotKey(None, index)


class mediaKeysHookerSignals(QObject):
	playPauseSignal = pyqtSignal()
	nextSongSignal = pyqtSignal()
	prevSongSignal = pyqtSignal()


class mediaKeysHooker(QRunnable):
	def __init__(self, main):
		super(mediaKeysHooker, self).__init__()
		self.signals = mediaKeysHookerSignals()
		self.main = main

	def run(self) -> None:
		print('beginning hotkey binding')
		GlobalHotKeys.register(0xB3, 0, self.playPause)
		GlobalHotKeys.register(0xB0, 0, self.nextSong)
		GlobalHotKeys.register(0xB1, 0, self.prevSong)
		print('listening for keybinds')
		GlobalHotKeys.listen()

	def playPause(self):
		print('received play/pause keypress')
		self.signals.playPauseSignal.emit()

	def nextSong(self):
		print('received next song keypress')
		self.signals.nextSongSignal.emit()

	def prevSong(self):
		print('received prev song keypress')
		self.signals.prevSongSignal.emit()
