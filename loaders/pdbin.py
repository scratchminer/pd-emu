from io import BytesIO
from os.path import splitext
from sys import argv

from loaders.pdfile import PDFile
from logger import init_logging, get_logger

LOGGER = get_logger("loaders.pdbin")

class PDBinFile(PDFile):
	
	MAGIC = b"Playdate PDX"
	MAGIC2 = b"Playdate BIN"
	PD_FILE_EXT = "pdex.bin"
	NONPD_FILE_EXT = ".elf"
	
	def __init__(self, filename, skip_magic=False):
		LOGGER.info(f"Converting {filename} to ELF...")
		super().__init__(filename, True)
		
		self.post2_0 = self.readbin(len(self.MAGIC)) in [self.MAGIC, self.MAGIC2]
		
		if self.post2_0:
			LOGGER.debug("Detected 2.0 binary format")
			
			self.advance(4)
			self.md5 = self.readbin(16)
			self.filesz = self.readu32()
			self.memsz = self.readu32()
			self.event_handler = self.readu32()
			relocs_len = self.readu32()
			
			self.decompress()
			self.code = self.readbin(self.code_size)
			self.relocs = []
			
			for i in range(relocs_len):
				self.relocs.append(self.readu32())
		else:
			LOGGER.debug("Detected legacy binary format")
			self.seek(0)
			
			self.event_handler = self.readu32() - 0x6000000c
			self.filesz = self.readu32() - 0x6000000c
			self.memsz = self.readu32() - 0x6000000c
			self.code = self.readbin(self.code_size)

	def to_elffile(self, revb=False):
		fh = BytesIO()
		
		SHSTRTAB = b"\0.text\0.bss\0.rel.text\0.symtab\0.strtab\0.shstrtab\0"
		
		# ELF header
		fh.write(b"\x7fELF\x01\x01\x01\0\0\0\0\0\0\0\0\0\x02\0\x28\0\x01\0\0\0")
		# Entry point
		fh.write(self.event_handler.to_bytes(4, byteorder="little"))
		# section header length
		fh.write(b"\x34\0\0\0")
		# section headers offset
		fh.write(((0x10021 + self.filesz + 8 * len(self.relocs) + len(SHSTRTAB) + 3) & ~3).to_bytes(4, byteorder="little"))
		# other necessary stuff
		fh.write(b"\0\x04\0\x05\x34\0\x20\0\x01\0\x28\0\x07\0\x06\0")
		
		# Program header
		fh.write(b"\x01\0\0\0\0\0\x01\0\0\0\0\0\0\0\0\0")
		# filesz and memsz
		fh.write(self.filesz.to_bytes(4, byteorder="little"))
		fh.write(self.memsz.to_bytes(4, byteorder="little"))
		fh.write(b"\x07\0\0\0\0\0\x01\0")
		
		# code
		while fh.tell() < 0x10000: fh.write(b"\0\0\0\0")
		fh.write(self.code)
		# relocation table
		for reloc in self.relocs:
			fh.write(reloc.to_bytes(4, byteorder="little"))
			fh.write(b"\x02\x01\0\0")
		# symbol table
		fh.write(b"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0")
		fh.write(b"\0\0\0\0\0\0\0\0\0\0\0\0\x00\0\x01\0")
		# string table placeholder
		fh.write(b"\0")
		# section name table
		fh.write(SHSTRTAB)
		
		# section headers
		while fh.tell() % 4 != 0: fh.write(b"\0")
		fh.write(b"\0\0\0\0" * 10)
		
		fh.write((SHSTRTAB.index(b".text\0")).to_bytes(4, byteorder="little"))
		fh.write(b"\x01\0\0\0\x37\0\0\0\0\0\0\0\0\0\x01\0")
		fh.write(self.filesz.to_bytes(4, byteorder="little"))
		fh.write(b"\0\0\0\0\0\0\0\0\x08\0\0\0\0\0\0\0")
		
		fh.write((SHSTRTAB.index(b".bss\0")).to_bytes(4, byteorder="little"))
		fh.write(b"\x08\0\0\0\x03\0\0\0")
		fh.write(self.filesz.to_bytes(4, byteorder="little"))
		fh.write((0x10000 + self.filesz).to_bytes(4, byteorder="little"))
		fh.write((self.memsz - filesz).to_bytes(4, byteorder="little"))
		fh.write(b"\0\0\0\0\0\0\0\0\x04\0\0\0\0\0\0\0")
		
		fh.write((SHSTRTAB.index(b".rel.text\0")).to_bytes(4, byteorder="little"))
		fh.write(b"\x09\0\0\0\x40\0\0\0\0\0\0\0")
		fh.write((0x10000 + self.filesz).to_bytes(4, byteorder="little"))
		fh.write((8 * len(self.relocs)).to_bytes(4, byteorder="little"))
		fh.write(b"\x04\0\0\0\x01\0\0\0\x04\0\0\0\x08\0\0\0")
		
		fh.write((SHSTRTAB.index(b".symtab\0")).to_bytes(4, byteorder="little"))
		fh.write(b"\x02\0\0\0\0\0\0\0\0\0\0\0")
		fh.write((0x10000 + self.filesz + 8 * len(self.relocs)).to_bytes(4, byteorder="little"))
		fh.write(b"\x20\0\0\0\x05\0\0\0\x02\0\0\0\x04\0\0\0\x10\0\0\0")
		
		fh.write((SHSTRTAB.index(b".strtab\0")).to_bytes(4, byteorder="little"))
		fh.write(b"\x03\0\0\0\0\0\0\0\0\0\0\0")
		fh.write((0x10020 + self.filesz + 8 * len(self.relocs)).to_bytes(4, byteorder="little"))
		fh.write(b"\x01\0\0\0\0\0\0\0\0\0\0\0\x01\0\0\0\0\0\0\0")
		
		fh.write((SHSTRTAB.index(b".shstrtab\0")).to_bytes(4, byteorder="little"))
		fh.write(b"\x03\0\0\0\0\0\0\0\0\0\0\0")
		fh.write((0x10021 + self.filesz + 8 * len(self.relocs)).to_bytes(4, byteorder="little"))
		fh.write(len(SHSTRTAB).to_bytes(4, byteorder="little"))
		fh.write(b"\0\0\0\0\0\0\0\0\x01\0\0\0\0\0\0\0")
		
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

# From my own research, as well as https://github.com/TheLogicMaster/Cranked/blob/master/src/Rom.cpp

# Version 2
# FILE HEADER (length 48):
# 0: char[12]: constant "Playdate PDX"
# 12: uint32: bitflags
# 16: byte[16]: MD5 hash of code
# 32: uint32: size of code
# 36: uint32: size of code + BSS
# 40: uint32: relative address of eventHandlerShim
# 44: uint32: number of relocation entries

# (compression boundary)

# code
# (relocation table: relative addresses are uint32, and relative to the beginning of the compressed data)

# Version 1
# FILE HEADER (length 12):
# 0: uint32: absolute address of eventHandlerShim
# 4: uint32: absolute code end address
# 8: uint32: absolute code + BSS end address

# code
