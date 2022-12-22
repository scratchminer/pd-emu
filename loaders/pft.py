import pygame as pg
import pygame.locals as pgloc
from PIL import Image

import io
from struct import unpack
from sys import argv
from unicodedata import category

from pdfile import PDFile
from pdi import PDImageFile, PDI_PALETTE_WITH_ALPHA, _flatten2d

PFT_PALETTE = _flatten2d(PDI_PALETTE_WITH_ALPHA)

class PDFontPage:
	def __init__(self, data, page_num):
		self.number = page_num
		
		self.glyphs_stored = []
		
		glyph_table = data[4:36]
		bits = 0
		for i in range(0x100):
			if i % 8 == 0: bits = glyph_table[i // 8]
			if (bits >> (i % 8)) & 1: 
				self.glyphs_stored.append((self.number << 8) | i)
		
		offset_table_length = 2 * len(self.glyphs_stored)
		offset_table = data[36:36 + offset_table_length]
		offsets = [0x0000]

		for i in range(0, offset_table_length, 2):
			offsets.append(unpack("<H", offset_table[i:i+2])[0])

		header_end = 36 + offset_table_length
		
		self.glyphs = {}
		for glyph_num in range(len(offsets) - 1):
			offset = offsets[glyph_num]
			next_offset = offsets[glyph_num + 1]

			self.glyphs[self.glyphs_stored[glyph_num]] = PDFontGlyph(data[header_end+offset+2:header_end+next_offset], self.glyphs_stored[glyph_num])

class PDFontGlyph:
	def __init__(self, data, glyph_num):
		self.width = data[0]
		self.codepoint = glyph_num
		self.utf8_char = chr(glyph_num)
		
		self.kerning_table = {}
		kerning_table_length = (data[1] + 1) * 2
		data = data[2:]
		
		for i in range(0, kerning_table_length, 2):
			self.kerning_table[chr(data[i])] = unpack("<b", bytes((data[i+1],)))[0]
		
		data = b"\0\0\0\0" + data[kerning_table_length:]
		
		self.image = PDImageFile(data, skip_magic=True)
		if not self.width: self.width = self.image.width

	def get_width(self, tracking, next_glyph="\0"):
		return tracking + self.image.width + self.kerning_table.get(next_glyph, 0)
	
	def get_top(self):
		return self.image.clip_t
	
	def to_surf(self, tracking, next_glyph="\0"):
		if not self.image.surf: self.image.to_surf()
		surf = self.image.surf
		glyph_width = tracking + self.image.width + self.kerning_table.get(next_glyph, 0)
		
		self.surf = pg.Surface((glyph_width, self.image.stored_height), pgloc.SRCALPHA)
		self.surf.blit(surf, (0, 0))
		
		return self.surf

	def to_pngfile(self, tracking, next_glyph="\0"):
		if not self.image.pil_img: self.image.to_pngfile()
		
		if self.image.height == 0:
			self.pil_img = Image.new("P", (self.image.stored_width, self.image.stored_height))
			self.pil_img.putpalette(PFT_PALETTE, "RGBA")
		else: self.pil_img = self.image.pil_img.copy()
				
		fh = io.BytesIO()
		self.pil_img.save(fh, format="PNG")
		self.pngfile = fh.getvalue()
		fh.close()

		return self.pngfile

class PDFontFile(PDFile):
	
	MAGIC = b"Playdate FNT"
	PD_FILE_EXT = ".pft"
	NONPD_FILE_EXT = ".png"

	def __init__(self, filename, skip_magic=False):
		super().__init__(filename, skip_magic)
						
		flags = self.readu32()
		compressed = bool(flags & 0x80000000)
		if compressed: self.advance(16)
		self.decompress(compressed)

		self.max_width = self.readu8()
		self.max_height = self.readu8()
		self.tracking = self.readu16()

		self.pages_stored = []
		bits = 0
		for i in range(0x200):
			if i % 8 == 0: bits = self.readu8()
			if (bits >> (i % 8)) & 1: self.pages_stored.append(i)

		offsets = [0x00000000]
		for i in range(len(self.pages_stored)):
			offsets.append(self.readu32())

		header_end = self.tell()

		self.pages = {}
		for page_num in range(len(offsets) - 1):
			self.seekrelto(header_end, offsets[page_num])

			offset = offsets[page_num]
			next_offset = offsets[page_num + 1]

			self.pages[self.pages_stored[page_num]] = PDFontPage(self.readbin(next_offset - offset), self.pages_stored[page_num])
	
	def get_glyph(self, glyph):
		if type(glyph) == str: glyph = ord(glyph)
		return self.pages[glyph >> 8].glyphs[glyph & 0xff]

	def get_width(self, text):
		text += "\0"

		return_accum = 0
		for i in range(len(text) - 1):
			char = text[i]
			if category(char) == "Zl" or char in "\r\n": return return_accum
			if category(char) in "CcCfCn": continue
			next_char = text[i + 1]
			return_accum += self.get_glyph(char).get_width(self.tracking, next_char)
		
		return return_accum

	def to_pngfile(self, text):
		text_width = self.get_width(text)
		text_height = self.max_height * (text.count("\n") + 1)
		
		pil_img = Image.new("P", (text_width, text_height))
		pil_img.putpalette(PFT_PALETTE, "RGBA")
		
		text += "\0"
		
		height_accum = 0
		width_accum = 0
		
		for i in range(len(text) - 1):
			char = text[i]
			next_char = text[i + 1]
			if char == "\n":
				height_accum += self.max_height
				width_accum = 0
				continue

			self.get_glyph(char).to_pngfile(self.tracking, next_char)			
			pil_img.paste(self.get_glyph(char).pil_img, (width_accum + self.tracking, height_accum))
			width_accum += self.get_glyph(char).get_width(self.tracking, next_char)

		fh = io.BytesIO()
		pil_img.save(fh, format="PNG")
		pngfile = fh.getvalue()
		fh.close()

		return pngfile

	def to_surf(self, text):
		text_width = self.get_width(text)
		text_height = self.max_height * (text.count("\n") + 1)
		
		surf = pg.Surface((text_width, text_height), pgloc.SRCALPHA)

		text += "\0"
		
		height_accum = 0
		width_accum = 0
		for i in range(len(text) - 1):
			char = text[i]
			next_char = text[i + 1]
			if char == "\n":
				height_accum += self.max_height
				width_accum = 0
				continue

			surf.blit(self.get_glyph(char).to_surf(self.tracking, next_char), (width_accum, height_accum))
			width_accum += self.get_glyph(char).get_width(self.tracking, next_char)

		return surf

	def to_nonpdfile(self):
		text = ""
		for page in self.pages.values():
			for glyph in page.glyphs.values():
				text += glyph.utf8_char
			text += "\n"

		text = text[:-1]
		return self.to_pngfile(text)

if __name__ == "__main__":
	fnt_file = PDFontFile(argv[1])
	with open(argv[1] + fnt_file.NONPD_FILE_EXT, "wb") as f:
		f.write(fnt_file.to_nonpdfile())

# From my own research, and also jaames/playdate-reverse-engineering#2

# FILE HEADER (length 16)
# 0: char[12]: constant "Playdate FNT"
# 12: uint32: file bitflags
# 		flags & 0x80000000 = file is compressed

# COMPRESSED FILE HEADER (length 16, inserted after the file header if the file is compressed)
# 0: uint32: decompressed data size in bytes
# 4: uint32: maximum glyph width
# 8: uint32: maximum glyph height 
# (4 bytes of zeros)

# OVERALL HEADER (length 68)
# 0: uint8: glyph width
# 1: uint8: glyph height
# 2: uint16: tracking
# 4: uint512: pages stored (bitmask)
#	 start at U+00xx
#	 if next bit (LSB first) = 0, the page isn't in this font
#	 otherwise, page is in this font as a standalone bank

# (offsets for pages are uint32)

# PAGE HEADER (length 36)
# (3 bytes of zeros)
# 3: uint8: number of glyphs in page
# 4: uint256: glyphs stored (bitmask)
#	 start at U+xx00
#	 if next bit (LSB first) = 0, character isn't in this font
#	 otherwise, character is in this page
	
# (offsets for glyphs are uint16)
		
# GLYPH FORMAT
# 0: uint8: advance this many pixels
# 1: uint8: number of kerning table entries - 1
# (kerning table)
# (image data for the glyph without the 16-byte header; see the PDI documentation)
