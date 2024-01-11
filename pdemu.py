from os import environ
from threading import Lock
from time import time, perf_counter

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = 1
import pygame as pg
import pygame.locals as pgloc

from loaders.pdx import PDXApplication
from logger import init_logging, get_logger

LOGGER = get_logger("pdemu")

class PDEmulator:
	class ButtonValues:
		LEFT = 0x01
		RIGHT = 0x02
		UP = 0x04
		DOWN = 0x08
		B = 0x10
		A = 0x20
		MENU = 0x40
		LOCK = 0x80
		
		BUTTON_STRINGS = {
			"a": A,
			"b": B,
			"up": UP,
			"down": DOWN,
			"left": LEFT,
			"right": RIGHT
		}
		
		def button_constant(button):
			if type(button) == str and button.lower() in PDEmulator.ButtonValues.BUTTON_STRINGS:
				return PDEmulator.ButtonValues.BUTTON_STRINGS[button.lower()]
			elif type(button) == int and button < 0x100: return button
			else:
				LOGGER.error("Invalid button constant value")
	
	def __init__(self, app=None):
		if type(app) == PDXApplication:
			# load it up
			pass
		pg.init()
		
		self.display = pg.display.set_mode(size=(400, 240), flags=pg.SCALED)
		self.reset()
	
	def reset(self):
		self.call_update_lock = Lock()
		self.newline = "\n"
		
		self.buttons = {
			PDEmulator.ButtonValues.LEFT: False,
			PDEmulator.ButtonValues.RIGHT: False,
			PDEmulator.ButtonValues.UP: False,
			PDEmulator.ButtonValues.DOWN: False,
			PDEmulator.ButtonValues.B: False,
			PDEmulator.ButtonValues.A: False,
			PDEmulator.ButtonValues.MENU: False,
			PDEmulator.ButtonValues.LOCK: False
		}
		self.prev_buttons = self.buttons.copy()
		
		self.clock = pg.time.Clock()
		self.game_time = 0.0
		self.hires_time = perf_counter()
		
		# self.accel =
		# self.battery =
		# self.crank =
		# self.fps_font =
		# self.gc =
		# self.serial =
		# self.settings =
		# self.stats =
		# self.system_menu =
		
	def __del__(self):
		pg.quit()