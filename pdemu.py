from os import environ
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = 1

import pygame as pg
import pygame.locals as pgloc

class PDEmulator:
	def __init__(self, app=None):
		if app is not None:
			# load it up
			pass
		