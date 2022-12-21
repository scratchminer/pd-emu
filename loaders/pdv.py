from PIL import Image, GifImagePlugin

import io
from sys import argv
from struct import unpack
from zlib import decompress

from pdfile import PDFile
from pdi import PDImageFile

PDV_PALETTE = (0x32, 0x2f, 0x28, 0xb1, 0xae, 0xa7)
PDV_BW_PALETTE = (0x00, 0x00, 0x00, 0xff, 0xff, 0xff)

PDV_FRAME_NONE = 0
PDV_FRAME_IFRAME = 1
PDV_FRAME_PFRAME = 2
PDV_FRAME_COMBINED = 3

GifImagePlugin.LOADING_STRATEGY = GifImagePlugin.LoadingStrategy.RGB_AFTER_DIFFERENT_PALETTE_ONLY

class PDVideoFile(PDFile):

	MAGIC = b"Playdate VID"
	PD_FILE_EXT = ".pdv"
	NONPD_FILE_EXT = ".gif"

	def __init__(self, filename, skip_magic=False):
		super().__init__(filename, skip_magic)

		self.advance(4)
		self.num_frames = self.readu16()
		self.advance(2)
		self.framerate = unpack("<f", self.readbin(4))[0]
		self.width = self.readu16()
		self.height = self.readu16()

		offsets = []
		frame_type_table = []
		self.frame_table = []

		for i in range(self.num_frames + 1):
			value = self.readu32()
			offsets.append(value >> 2)
			frame_type_table.append(value & 0x3)
		
		header_end = self.tell()

		for i in range(len(offsets) - 1):
			offset = offsets[i]
			next_offset = offsets[i + 1]
			self.seekrelto(header_end, offset)
			
			frame_data = decompress(self.readbin(next_offset - offset))
			if frame_type_table[i] == PDV_FRAME_IFRAME:
				self.frame_table.append(PDImageFile.from_bytes(frame_data, self.width, self.height))
			elif frame_type_table[i] == PDV_FRAME_PFRAME:
				prev_frame = self.frame_table[-1]
				
				frame_data = bytearray(frame_data)
				for i in range(len(frame_data)):
					frame_data[i] ^= prev_frame.raw[i]
				frame_data = bytes(frame_data)
				
				img_file = PDImageFile.from_bytes(frame_data, self.width, self.height)
				
				self.frame_table.append(img_file)
			elif frame_type_table[i] == PDV_FRAME_COMBINED:
				iframe_len = unpack("<H", frame_data[:2])[0]
				iframe_len = iframe_len[2:]
				iframe_file = frame_data[:iframe_len]
				pframe_file = PDImageFile.from_bytes(frame_data[iframe_len:], self.width, self.height)
				
				iframe_file = bytearray(iframe_file)
				for i in range(len(iframe_file.raw)):
					iframe_file[i] ^= pframe_file.raw[i]
				iframe_file = bytes(iframe_file)

				self.frame_table.append(iframe_file)

	def to_surflist(self):
		return_list = []
		for i in range(len(self.frame_table)):
			return_list.append(self.frame_table[i].to_surf())
		return return_list

	def to_giffile(self, bw=False):
		for i in range(len(self.frame_table)):
			self.frame_table[i].to_pngfile()
		
		if bw: pal = PDV_BW_PALETTE
		else: pal = PDV_PALETTE
		frame_duration = round(1000 / self.framerate)
		
		pil_img_list = []
		for img in self.frame_table:
			pil_img_list.append(img.pil_img.convert(dither=Image.Dither.NONE))
		
		fh = io.BytesIO()
		pil_img_list[0].save(fh, format="GIF", save_all=True, append_images=pil_img_list[1:], duration=frame_duration)
		self.giffile = fh.getvalue()
		fh.close()

		return self.giffile

	def to_nonpdfile(self):
		return self.to_giffile()

if __name__ == "__main__":
	filename = argv[1]
	vid_file = PDVideoFile(filename)
	with open(filename + vid_file.NONPD_FILE_EXT, "wb") as f:
		f.write(vid_file.to_giffile())