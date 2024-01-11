import logging

def init_logging(level=logging.INFO):
	logging.basicConfig(style="{", format="[{levelname}] {name}: {message}")

def get_logger(name):
	return logging.getLogger(name)