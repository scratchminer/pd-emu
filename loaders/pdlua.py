from api.runtime import RUNTIME
from sys import argv

from loaders.pdfile import PDFile
from logger import init_logging, get_logger

LOGGER = get_logger("loaders.pdlua")

def _filter(obj, attr_name, setting):
	raise AttributeError

class PDLuaBytecodeFile(PDFile):
	MAGIC = b"\x1bLua\x54\x00\x19\x93\r\n\x1a\n\x04\x04\x04" # Lua 5.4.0 release
	MAGIC2 = b"\x1bLua\x03\xf8\x00\x19\x93\r\n\x1a\n\x04\x04\x04" # Lua 5.4.0 beta
	PD_FILE_EXT = ""
	NONPD_FILE_EXT = ".luac"
	
	def __init__(self, filename, parent_pdz, skip_magic=False):
		if not skip_magic: LOGGER.info(f"Decompiling Lua bytecode file {filename}...")
		super().__init__(filename, skip_magic)
		
		self.parent_pdz = parent_pdz
		self.seek(0)
		self.runtime = RUNTIME
	
	def execute(self, *args):
		self.runtime.set_global("import", self.import_func)
		result = self.runtime.execute(self.readbin(), *args)
		self.seek(0)
		return result
	
	def import_func(self, lib_name):
		self.parent_pdz.import_func(lib_name)
	
	def to_nonpdfile(self):
		data = self.readbin()
		self.seek(0)
		return data

if __name__ == "__main__":
	init_logging()
	
	filename = argv[1]
	lua_file = PDLuaBytecodeFile(filename)
	LOGGER.warning("This file is Playdate Lua bytecode. You'll need a Lua decompiler to obtain the Lua source.")
	with open(filename + lua_file.NONPD_FILE_EXT, "wb") as f:
		f.write(lua_file.to_nonpdfile())
