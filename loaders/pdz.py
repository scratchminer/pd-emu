from os import mkdir, sep as PATHSEP
from os.path import abspath, basename, join as joinpath, normpath, splitext
from sys import argv
from zlib import decompress

from loaders.pdfile import PDFile
from loaders.pdlua import PDLuaBytecodeFile
from loaders.pda import PDAudioFile
from loaders.pdi import PDImageFile
from loaders.pds import PDStringsFile
from loaders.pdt import PDImageTableFile
from loaders.pdv import PDVideoFile
from loaders.pft import PDFontFile

PDZ_FILE_NONE = 0
PDZ_FILE_LUABYTECODE = 1
PDZ_FILE_IMAGE = 2
PDZ_FILE_IMAGETABLE = 3
PDZ_FILE_VIDEO = 4
PDZ_FILE_AUDIO = 5
PDZ_FILE_STRINGS = 6
PDZ_FILE_FONT = 7

class PDZipEntry:
	def __init__(self, parent_pdz, filename, filetype=PDZ_FILE_NONE, data=bytes()):
		
		self.filename = filename
		self.filetype = filetype
		self.is_directory = False
		self.parent_pdz = parent_pdz
		
		if filetype == PDZ_FILE_NONE:
			self.data = {}
			self.is_directory = True
			self.extension = ""
		elif filetype == PDZ_FILE_LUABYTECODE:
			self.data = PDLuaBytecodeFile(data, parent_pdz)
		elif filetype == PDZ_FILE_IMAGE:
			self.data = PDImageFile(b"\0\0\0\0" + data, skip_magic=True)
		elif filetype == PDZ_FILE_IMAGETABLE:
			self.data = PDImageTableFile(b"\0\0\0\0" + data, skip_magic=True)
		elif filetype == PDZ_FILE_VIDEO:
			self.data = PDVideoFile(b"\0\0\0\0" + data, skip_magic=True)
		elif filetype == PDZ_FILE_AUDIO:
			self.data = PDAudioFile(data, skip_magic=True)
		elif filetype == PDZ_FILE_STRINGS:
			self.data = PDStringsFile(b"\0\0\0\0" + data, skip_magic=True)
		elif filetype == PDZ_FILE_FONT:
			self.data = PDFontFile(b"\0\0\0\0" + data, skip_magic=True)
		else: raise ValueError("Unknown file type value %i" % filetype)
		
		if filetype > PDZ_FILE_NONE: self.extension = self.data.NONPD_FILE_EXT

	def add_file(self, filename, filetype=PDZ_FILE_NONE, data=bytes()):		
		if self.is_directory:
			path = normpath(filename).split("/")
			directory = self
			
			for i in range(len(path) - 1):
				try: directory = directory.data[path[i]]
				except KeyError:
					if path[i] == "": continue
					directory.add_file(path[i], PDZ_FILE_NONE)
					directory = directory.data[path[i]]
			
			directory.data[path[-1]] = PDZipEntry(self.parent_pdz, path[-1], filetype, data)
		else: raise ValueError("Entry not a directory")

	def get_file(self, filename):
		path = normpath(filename).split("/")
		directory = self
		
		for i in range(len(path) - 1):
			try: directory = directory.data[path[i]]
			except KeyError: raise FileNotFoundError(f"Entry not found: '{path[i]}'")

		try: return directory.data[path[-1]]
		except KeyError: raise FileNotFoundError(f"Entry not found: '{path[-1]}'")

	def dump_files(self, path):
		try: mkdir(path)
		except FileExistsError: pass
		
		for filename in self.data.keys():
			target = self.data[filename]			
			if target.is_directory:
				target.dump_files(joinpath(path, target.filename))
			else:
				if target.filetype > PDZ_FILE_NONE: non_pdfile = target.data.to_nonpdfile()
				else: non_pdfile = target.data
				
				if type(non_pdfile) == list:
					for i in range(1, len(non_pdfile) + 1):
						filename = f"{target.filename}-table-{i}{target.extension}"
						with open(joinpath(path, filename), "wb") as f:
							f.write(non_pdfile[i - 1])
				else:
					filename = target.filename + target.extension
					with open(joinpath(path, filename), "wb") as f:
						f.write(non_pdfile)

class PDZipFile(PDFile):

	MAGIC = b"Playdate PDZ"
	PD_FILE_EXT = ".pdz"

	def __init__(self, filename, skip_magic=False):
		super().__init__(filename, skip_magic)
		
		self.advance(4)
		self.root_directory = PDZipEntry(self, "", PDZ_FILE_NONE)
		self.imported_files = []
		
		flags = self.readu8()
		
		while flags is not None:
			compressed = bool(flags & 0x80)
			filetype = flags & 0x7f
	
			file_length = self.readu24()
			filename = self.readstr()
			
			self.align(4)
			
			data = self.readbin(file_length)
			
			if compressed:
				if filetype == PDZ_FILE_AUDIO:
					# Audio files have the sample rate and audio format uncompressed out front
					data = data[:4] + decompress(data[8:])
				else: data = decompress(data[4:])
			
			self.root_directory.add_file(filename, filetype, data)
			flags = self.readu8()
	
	def import_func(self, path):
		if path not in self.imported_files:
			self.imported_files.append(path)
			self.get_file(path).execute()
			
	def get_file(self, path):
		return self.root_directory.get_file(path)

	def dump_files(self, directory_name):
		self.root_directory.dump_files(directory_name)

if __name__ == "__main__":
	filename = argv[1]
	pdz_file = PDZipFile(filename)
	dump_loc = splitext(filename)[0]
	if len(argv) > 2: dump_loc = abspath(argv[2])
	
	pdz_file.dump_files(dump_loc)

# From jaames/playdate-reverse-engineering, and also some of my own research

# FILE HEADER (length 16)
# 0: char[12]: constant "Playdate PDZ"
# (4 bytes of zeros)

# FILE ENTRY
# uint8: file bitflags
# 		flags & 0x80 = file is compressed
# 		flags & 0x7F = file type
# 			0 = none
# 			1 = Playdate Lua bytecode
# 			2 = image (PDI)
# 			3 = image table (PDT)
# 			4 = video (PDV)
# 			5 = audio (PDA)
# 			6 = strings (PDS)
# 			7 = font (PFT)
# uint24: total data length
# char *: filename, null-terminated
# (padding to align to a multiple of 4 bytes)
# uint24: audio sample rate in Hz (present only if the file is a compressed audio file)
# enum SoundFormat: audio data format (present only if the file is a compressed audio file)
# uint32: data length when decompressed (if the data is compressed, this is present and included in the data length)
# (entry data)