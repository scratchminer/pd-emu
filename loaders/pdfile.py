from io import BytesIO
from zlib import decompress
from struct import unpack, error as struct_error

class PDFile:
	def __init__(self, filename, skip_magic, mode="rb"):
		self.filename = filename
		self.data = b""
		if type(filename) == str:
			with open(filename, mode) as f: self.data = f.read()
		else:
			self.data = filename
		self.handle = BytesIO(self.data)
		
		if not skip_magic:
			if not hasattr(self, "MAGIC2") and self.readbin(len(self.MAGIC)) != self.MAGIC: raise ValueError("incorrect magic number for Playdate file")
			elif hasattr(self, "MAGIC2"):
				if (self.data[:len(self.MAGIC)] == self.MAGIC):
					self.fallback = False
					self.advance(len(self.MAGIC))
				elif (self.data[:len(self.MAGIC2)] == self.MAGIC2):
					self.fallback = True
					self.advance(len(self.MAGIC2))
				else: raise ValueError("incorrect magic number for Playdate file")
	def decompress(self, compressed=True):
		self.compressed = compressed
		if self.compressed:
			self.zlib_data = decompress(self.handle.read())
			self.handle.close()
			self.handle = BytesIO(self.zlib_data)
	def readbin(self, numbytes=-1):
		return self.handle.read(numbytes)
	def readu8(self):
		try: return unpack("<B", self.readbin(1))[0]
		except struct_error: return None
	def reads8(self):
		try: return unpack("<b", self.readbin(1))[0]
		except struct_error: return None
	def readu16(self):
		try: return unpack("<H", self.readbin(2))[0]
		except struct_error: return None
	def reads16(self):
		try: return unpack("<h", self.readbin(2))[0]
		except struct_error: return None
	def readu24(self):
		try: return int.from_bytes(self.readbin(3), byteorder="little")
		except struct_error: return None
	def readu32(self):
		try: return unpack("<L", self.readbin(4))[0]
		except struct_error: return None
	def readstr(self):
		b = bytes()
		while True:
			byte = self.readbin(1) 
			if byte == bytes(): break
			if unpack("<B", byte)[0] == 0: break
			b += byte
		return str(b, encoding="utf-8")
	def seek(self, offset):
		self.handle.seek(offset)
	def seekrelto(self, pos, offset):
		self.handle.seek(pos + offset)
	def tell(self):
		return self.handle.tell()
	def advance(self, numbytes):
		self.handle.seek(numbytes, 1)
	def align(self, numbytes):
		while self.tell() % numbytes != 0: self.advance(1)
	def is_eof(self):
		b = self.readu8()
		self.seekrelto(self.tell(), -1)
		return b is None
	def close(self):
		self.handle.close()
	def __del__(self):
		self.close()
