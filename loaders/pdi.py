import pygame as pg
import pygame.locals as pgloc
from PIL import Image

from io import BytesIO
from math import ceil
from struct import pack
from sys import argv

from loaders.pdfile import PDFile

PDI_PALETTE = (
	(0x32, 0x2f, 0x28),
	(0xb1, 0xae, 0xa7)
)

PDI_PALETTE_WITH_ALPHA = (
	(0x32, 0x2f, 0x28, 0x00),
	(0xb1, 0xae, 0xa7, 0x00),
	(0x32, 0x2f, 0x28, 0xff),
	(0xb1, 0xae, 0xa7, 0xff)
)

PDI_BW_PALETTE = (
	(0x00, 0x00, 0x00),
	(0xff, 0xff, 0xff)
)

PDI_BW_PALETTE_WITH_ALPHA = (
	(0x00, 0x00, 0x00, 0x00),
	(0xff, 0xff, 0xff, 0x00),
	(0x00, 0x00, 0x00, 0xff),
	(0xff, 0xff, 0xff, 0xff),
)

def _flatten2d(seq):
	return_seq = []
	
	for i in range(len(seq)):
		for j in range(len(seq[i])):
			return_seq.append(seq[i][j])
	
	return return_seq

class PDImageFile(PDFile):
	
	MAGIC = b"Playdate IMG"
	PD_FILE_EXT = ".pdi"
	NONPD_FILE_EXT = ".png"
	
	def __init__(self, filename, skip_magic=False):
		super().__init__(filename, skip_magic)
		
		if filename != bytes():
			flags = self.readu32()
			compressed = bool(flags & 0x80000000)
			if compressed: self.advance(16)
			self.decompress(compressed)
			
			self.width = self.readu16()
			self.height = self.readu16()
			self.stride = self.readu16()
			self.clip_l = self.readu16()
			self.clip_r = self.readu16()
			self.clip_t = self.readu16()
			self.clip_b = self.readu16()
			flags = self.readu16()
			self.alpha = bool(flags & 0x3)
			
			data_start = self.tell()
			self.raw = self.readbin()
			self.seek(data_start)
			
			self.pil_img = None
			self.surf = None
			self.pixels = []
			
			should_alpha = bool(self.clip_l or self.clip_r or self.clip_t or self.clip_b)
			
			self.stored_width = self.width + self.clip_l + self.clip_r
			self.stored_height = self.height + self.clip_t + self.clip_b
			
			for y in range(self.clip_t):
				self.pixels.append([0] * self.stored_width)
			
			for y in range(self.clip_t, self.height + self.clip_t):
				self.pixels.append([])
				row = self.readbin(self.stride)
				
				for x in range(self.clip_l):
					self.pixels[y].append(0x0)
					
				for x in range(self.clip_l, self.width + self.clip_l):
					x_rel = x - self.clip_l
					
					self.pixels[y].append((row[x_rel // 8] >> (7-(x_rel%8))) & 0x1)
					self.pixels[y][x] |= (int(should_alpha) << 0x1)
				
				for x in range(self.clip_r):
					self.pixels[y].append(0x0)
				
			for y in range(self.clip_b):
				self.pixels.append([0] * self.stored_width)
			
			if self.alpha or should_alpha:				
				for y in range(self.clip_t, self.height + self.clip_t):					
					if self.alpha: 
						row = self.readbin(self.stride)
						while len(row) != self.stride: row += b"\0"
					
					for x in range(self.clip_l, self.width + self.clip_l):
						x_rel = x - self.clip_l
						
						self.pixels[y][x] &= 0x1
						if self.alpha: self.pixels[y][x] |= ((row[x_rel // 8] >> (7-(x_rel%8))) & 0x1) << 1
						else: self.pixels[y][x] |= 0x2
	
	def to_surf(self):
		self.surf = pg.Surface((len(self.pixels), len(self.pixels[0])), flags=(self.alpha * pgloc.SRCALPHA))
		arr = pg.PixelArray(self.surf)
		
		for y in range(len(self.pixels)):
			for x in range(len(self.pixels[y])):
				if self.alpha:
					arr[x][y] = PDI_PALETTE_WITH_ALPHA[self.pixels[y][x]]
				else:
					arr[x][y] = PDI_PALETTE[self.pixels[y][x]]
		del arr
		
		return self.surf

	def to_pngfile(self, bw=False):
		if self.alpha: 
			color = "RGBA"	
			if bw: self.palette = _flatten2d(PDI_BW_PALETTE_WITH_ALPHA)
			else: self.palette = _flatten2d(PDI_PALETTE_WITH_ALPHA)
		else:
			color = "RGB"
			if bw: self.palette = _flatten2d(PDI_BW_PALETTE)
			else: self.palette = _flatten2d(PDI_PALETTE)
		
		self.pil_img = Image.new("P", (self.stored_width, self.stored_height))
		self.pil_img.putpalette(self.palette, color)
		self.pil_img.putdata(_flatten2d(self.pixels))

		fh = BytesIO()
		self.pil_img.save(fh, format="PNG")
		self.pngfile = fh.getvalue()
		fh.close()

		return self.pngfile

	def to_nonpdfile(self):
		return self.to_pngfile()

	@staticmethod
	def from_bytes(data, width, height, has_alpha=False):
		header = pack("<L", 0x00000000)
		
		header += pack("<H", width)
		header += pack("<H", height)
		header += pack("<H", ceil(width / 8))

		header += pack("<H", 0x0000)
		header += pack("<H", 0x0000)
		header += pack("<H", 0x0000)
		header += pack("<H", 0x0000)

		header += pack("<H", 0x3 * int(has_alpha))
		
		img_file = PDImageFile(header + data, skip_magic=True)
		
		return img_file

if __name__ == "__main__":
	filename = argv[1]
	img_file = PDImageFile(filename)
	with open(filename + img_file.NONPD_FILE_EXT, "wb") as f:
		f.write(img_file.to_pngfile(bw=False))

# From jaames/playdate-reverse-engineering

# FILE HEADER (length 16)
# 0: char[12]: constant "Playdate IMG"
# 12: uint32: file bitflags
# 		flags & 0x80000000 = file is compressed

# COMPRESSED FILE HEADER (length 16, inserted after the file header if the file is compressed)
# 0: uint32: decompressed data size in bytes
# 4: uint32: image width
# 8: uint32: image height
# (4 bytes of zeros)

# IMAGE DATA HEADER (length 16)
# 0: uint16: stored image width
# 2: uint16: stored image height
# 4: uint16: image stride (usually ceil(width / 8))
# 6: uint16: size of transparent left padding
# 8: uint16: size of transparent right padding
# 10: uint16: size of transparent top padding
# 12: uint16: size of transparent bottom padding
# 14: uint16: image bitflags
# 		flags & 0x3 = image contains a separate alpha map

# (data for the black/white map, with 0 = black and 1 = white)
# (if the image contains one, data for the alpha map, with 0 = transparent and 1 = opaque)
