from sys import argv

from pdfile import PDFile
from pdi import PDImageFile

class PDImageTableFile(PDFile):

	MAGIC = b"Playdate IMT"
	PD_FILE_EXT = ".pdt"
	NONPD_FILE_EXT = ".png"

	def __init__(self, filename, skip_magic=False):
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
		else:
			self.is_matrix = False
			self.num_rows = 1

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
		return self.image_table

	def to_list(self):
		return_list = []
		
		for y in range(self.num_rows):
			for x in range(self.num_per_row):
				return_list.append(self.image_table[y][x])
		return return_list

	def to_nonpdfile(self):
		return_list = []
				
		for y in range(self.num_rows):
			for x in range(self.num_per_row):
				return_list.append(self.image_table[y][x].to_pngfile())

		return return_list

if __name__ == "__main__":
	filename = argv[1]
	imt_file = PDImageTableFile(filename)
	img_list = imt_file.to_nonpdfile()
	for i in range(len(img_list)):
		with open(f"{filename}-frame{i}" + imt_file.NONPD_FILE_EXT, "wb") as f:
			f.write(img_list[i])
