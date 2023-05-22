from json import dumps
from os.path import splitext
from sys import argv

from loaders.pdfile import PDFile
from logger import init_logging, get_logger

LOGGER = get_logger("loaders.pds")

class PDStringsFile(PDFile):
	
	MAGIC = b"Playdate STR"
	PD_FILE_EXT = ".pds"
	NONPD_FILE_EXT = ".strings"
	
	def __init__(self, filename, skip_magic=False):
		if not skip_magic: LOGGER.info(f"Decompiling strings file {filename}...")
		super().__init__(filename, skip_magic)
		
		flags = self.readu32()
		compressed = bool(flags & 0x80000000)
		if compressed: self.advance(16)
		self.decompress(compressed)
		
		self.num_keys = self.readu32()
		offsets = [0x00000000]
		self.string_table = {}
		
		for i in range(self.num_keys - 1):
			offsets.append(self.readu32())
		header_end = self.tell()
		
		for i in range(len(offsets) - 1):
			self.seekrelto(header_end, offsets[i])
			k = self.readstr()
			v = self.readstr()
			self.string_table[k] = v
	
	def to_dict(self):
		return self.string_table
	
	def to_stringsfile(self):
		data = b"-- Decompiled with the pd-emu decompilation tools"
		for k, v in self.string_table.items():
			data += f"\n\"{k}\" = \"{v}\"".encode("utf-8")
		self.stringsfile = data
		return self.stringsfile
	
	def to_nonpdfile(self):
		return self.to_stringsfile()

if __name__ == "__main__":
	init_logging()
	
	filename = argv[1]
	str_file = PDStringsFile(filename)
	with open(f"{splitext(filename)[0]}{str_file.NONPD_FILE_EXT}", "wb") as f:
		f.write(str_file.to_nonpdfile())

# From jaames/playdate-reverse-engineering

# FILE HEADER (length 16)
# 0: char[12]: constant "Playdate STR"
# 12: uint32: file bitflags
# 		flags & 0x80000000 = file is compressed

# COMPRESSED FILE HEADER (length 16, inserted after the file header if the file is compressed)
# 0: uint32: decompressed data size in bytes
# (12 bytes of zeros)

# STRING TABLE HEADER (length 2)
# 0: uint32: number of table entries

# (offsets for table entries are uint32)

# ENTRY FORMAT
# char *: key, null-terminated
# char *: value, null-terminated