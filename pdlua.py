import copy
from sys import argv

from pdfile import PDFile

from lupa_pd import LuaRuntime

def _filter(obj, attr_name, setting):
	raise AttributeError

RUNTIME = LuaRuntime(register_builtins=False, attribute_filter=_filter, unpack_returned_tuples=False)

class PDLuaBytecodeFile(PDFile):
	
	MAGIC = b"\x1bLua\x54\x00\x19\x93\r\n\x1a\n\x04\x04\x04" # Lua 5.4.0 release
	MAGIC2 = b"\x1bLua\xf8\x03\x00\x19\x93\r\n\x1a\n\x04\x04\x04" # Lua 5.4.0 beta
	PD_FILE_EXT = ""
	NONPD_FILE_EXT = ".luac"
	
	def __init__(self, filename, skip_magic=False):
		super().__init__(filename, skip_magic)
		self.seek(0)
		self.runtime = RUNTIME
	
	def execute(self, *args):
		result = self.runtime.execute(self.readbin(), *args)
		self.seek(0)
		return result
	
	def to_nonpdfile(self):
		data = self.readbin()
		self.seek(0)
		return data

if __name__ == "__main__":
	filename = argv[1]
	lua_file = PDLuaBytecodeFile(filename)
	if lua_file.fallback: print("[WARNING] This file is Lua 5.4.0-beta bytecode. You'll need unluac or a similar program to decompile this.")
	with open(filename + lua_file.NONPD_FILE_EXT, "wb") as f:
		f.write(lua_file.to_nonpdfile())