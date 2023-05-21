from PIL import Image

from io import BytesIO
from os.path import splitext
from sys import argv

from loaders.pdfile import PDFile
from loaders.pdi import PDImageFile
from logger import init_logging, get_logger

LOGGER = get_logger("loaders.pdt")

class PDImageTableFile(PDFile):

	MAGIC = b"Playdate IMT"
	PD_FILE_EXT = ".pdt"
	NONPD_FILE_EXT = ".png"

	def __init__(self, filename, skip_magic=False):
		if not skip_magic: LOGGER.info(f"Decompiling image table file {filename}...")
		super().__init__(filename, skip_magic)

		flags = self.readu32()
		compressed = bool(flags & 0x80000000)
		if compressed: self.advance(16)
		self.decompress(compressed)

		self.num_images = self.readu16()
		self.num_per_row = self.readu16()
		
		if self.num_images != self.num_per_row and self.num_per_row != 0:
			self.is_matrix = True
			self.num_rows = self.num_images // self.num_per_row
			LOGGER.debug(f"Matrix table, image count: {self.num_per_row} x {self.num_rows} images")
		else:
			self.is_matrix = False
			self.num_rows = 1
			LOGGER.debug(f"Sequential table, image count: {self.num_per_row} images")

		offsets = [0x00000000]
		self.image_table = []

		for i in range(self.num_images):
			offsets.append(self.readu32())

		header_end = self.tell()

		for y in range(self.num_rows):
			self.image_table.append([])
			for x in range(self.num_per_row):
				offset = offsets[y * self.num_per_row + x]
				next_offset = offsets[1 + (y * self.num_per_row + x)]
				self.seekrelto(header_end, offset)
				self.image_table[y].append(PDImageFile(b"\0\0\0\0" + self.readbin(next_offset - offset), skip_magic=True))

	def to_matrix(self):
		self.pil_img = Image.new("RGBA", (self.num_per_row * self.image_table[0][0].stored_width, self.num_rows * self.image_table[0][0].stored_height))
		
		for y in range(self.num_rows):
			for x in range(self.num_per_row):
				self.image_table[y][x].to_pngfile()
				self.pil_img.paste(self.image_table[y][x].pil_img, (x * self.image_table[y][x].stored_width, y * self.image_table[y][x].stored_height))
		fh = BytesIO()
		self.pil_img.save(fh, format="PNG")
		matrix = fh.getvalue()
		fh.close()
		
		return matrix

	def to_list(self):
		return_list = []
		
		for y in range(self.num_rows):
			for x in range(self.num_per_row):
				return_list.append(self.image_table[y][x])
		return return_list

	def to_nonpdfile(self):
		if self.is_matrix: return self.to_matrix()
		else: return self.to_list()

if __name__ == "__main__":
	init_logging()
	
	filename = argv[1]
	imt_file = PDImageTableFile(filename)
	img_list = imt_file.to_nonpdfile()
	if not imt_file.is_matrix:
		for i in range(len(img_list)):
			with open(f"{splitext(filename)[0]}-table-{i}{imt_file.NONPD_FILE_EXT}", "wb") as f:
				f.write(img_list[i])
	else:
		with open(f"{splitext(filename)[0]}-table-{imt_file.image_table[0][0].stored_width}-{imt_file.image_table[0][0].stored_height}{imt_file.NONPD_FILE_EXT}", "wb") as f:
			f.write(img_list)

# From jaames/playdate-reverse-engineering

# FILE HEADER (length 16)
# 0: char[12]: constant "Playdate IMT"
# 12: uint32: file bitflags
# 		flags & 0x80000000 = file is compressed

# COMPRESSED FILE HEADER (length 16, inserted after the file header if the file is compressed)
# 0: uint32: decompressed data size in bytes
# 4: uint32: width of the first cell
# 8: uint32: height of the first cell
# 12: uint32: total number of cells

# TABLE HEADER (length 4):
# 0: uint16: total number of cells
# 2: uint16: number of cells on each row

# (offsets for cells are uint32)

# (data, see image format)