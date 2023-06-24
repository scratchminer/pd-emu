from io import BytesIO
from os.path import splitext
from sys import argv

from loaders.pdfile import PDFile
from logger import init_logging, get_logger

LOGGER = get_logger("loaders.pdbin")

class PDBinFile(PDFile):
	
	MAGIC = b"Playdate PDX"
	PD_FILE_EXT = "pdex.bin"
	NONPD_FILE_EXT = ".elf"
	
	def __init__(self, filename, skip_magic=False):
		if not skip_magic: LOGGER.info(f"Decompiling {filename}...")
		super().__init__(filename, skip_magic)
		
		self.advance(4)
		self.md5 = self.readbin(16)
		self.bss_start = self.readu32()
		self.bss_end = self.readu32()
		
		LOGGER.debug(f"__bss_start__: offset 0x{self.bss_start:08x}")
		LOGGER.debug(f"__bss_end__: offset 0x{self.bss_end:08x}")
		LOGGER.debug(f"Unknown values: {self.readu32():08x} and {self.readu32():08x}")
		
		self.decompress()

	def to_elffile(self, bw=False):
		fh = BytesIO()
		
		# convert to elf (todo)
		
		self.elffile = fh.getvalue()
		fh.close()

		return self.elffile
	
	def to_nonpdfile(self):
		return self.to_elffile()

if __name__ == "__main__":
	init_logging()
	
	filename = argv[1]
	bin_file = PDBinFile(filename)
	with open(f"{splitext(filename)[0]}{bin_file.NONPD_FILE_EXT}", "wb") as f:
		f.write(bin_file.to_nonpdfile())

# From my own research

# FILE HEADER (length 48):
# 0: char[12]: constant "Playdate PDX"
# (4 bytes of zeros)
# 16: byte[16]: MD5 hash of something?
# 32: uint32: BSS start
# 36: uint32: BSS end
# 40: uint32: unknown
# 44: uint32: unknown

# (compression boundary)

# .text section
# .data section
# (symbol offset table: offsets are uint32, and relative to the beginning of the compressed data)

