from io import BytesIO
from sys import argv, byteorder as BYTEORDER

import loaders._wave as wave
from loaders.pdfile import PDFile

MONO_8 = 0
STEREO_8 = 1
MONO_16 = 2
STEREO_16 = 3
MONO_ADPCM4 = 4
STEREO_ADPCM4 = 5
FORMAT_LENGTH = 6

class PDAudioFormat:
	@staticmethod
	def get_nchannels(fmt):
		if fmt >= FORMAT_LENGTH: raise ValueError("not a valid Playdate audio format")
		return (fmt & 1) + 1
	
	@staticmethod
	def get_sampwidth(fmt):
		if fmt < MONO_16: return 1
		elif fmt < MONO_ADPCM4: return 2
		elif fmt < FORMAT_LENGTH: return 2
		else: raise ValueError("not a valid Playdate audio format")

class PDAudioFile(PDFile):
	
	MAGIC = b"Playdate AUD"
	PD_FILE_EXT = ".pda"
	NONPD_FILE_EXT = ".wav"
	
	def __init__(self, filename, skip_magic=False):
		super().__init__(filename, skip_magic)
		
		self.framerate = self.readu24()	
		self.fmt = self.readu8()
	
	def to_wavfile(self):			
		fh = BytesIO()
		
		self.nchannels = PDAudioFormat.get_nchannels(self.fmt)
		self.sampwidth = PDAudioFormat.get_sampwidth(self.fmt)
		
		wavfile = wave.open(fh, "wb", wave.WAVE_FORMAT_PCM if self.fmt < MONO_ADPCM4 else wave.WAVE_FORMAT_ADPCM)
		
		wavfile.setnchannels(self.nchannels)
		wavfile.setsampwidth(self.sampwidth)
		wavfile.setframerate(self.framerate)
		
		data = bytes()
		stereo = (self.nchannels == 2)
		if self.fmt < MONO_ADPCM4: data = self.readbin()
		elif self.fmt < FORMAT_LENGTH:
			wavfile.block_size = self.readu16()
			
			if self.nchannels == 1:
				# no conversion needed -- the samples are already in the correct format
				data = self.readbin()
			else:
				# uh-oh, we have to shuffle the samples around to make them work with the WAV format
				# this is the fastest way I could think of to do it
				saved_pos = self.tell()
				self.handle.seek(0, 2)
				file_end = self.tell()
				self.seek(saved_pos)
				
				def _process_small(blk, is_header):
					if is_header: return blk
					ret = [(blk[2*i] >> 4) | (blk[2*i + 1] & 0xf0) for i in range(4)]
					ret.extend([(blk[2*i] & 0x0f) | ((blk[2*i + 1] << 4) & 0xf0) for i in range(4)])
					return bytes(ret)
				
				blocks = [self.readbin(8) for num in range(saved_pos, file_end, 8)]
				data = bytes().join(map(
					_process_small,
					blocks,
					[(num - saved_pos) % wavfile.block_size == 0 for num in range(saved_pos, file_end, 8)]
				))
		wavfile.writeframes(data)
		wavfile.close()
		self.wavfile = fh.getvalue()
		fh.close()
		
		return self.wavfile
	def to_nonpdfile(self):
		return self.to_wavfile()

if __name__ == "__main__":
	filename = argv[1]
	aud_file = PDAudioFile(filename)
	with open(filename + aud_file.NONPD_FILE_EXT, "wb") as f:
		f.write(aud_file.to_wavfile())

# From my own research, but also jaames/playdate-reverse-engineering

# FILE HEADER (length 16, but outside the compressed area if this file is contained in a PDZ)
# 0: char[12]: constant "Playdate AUD"
# 12: uint24: sample rate in Hz
# 15: enum SoundFormat: sound format
# 		0 = mono 8-bit PCM
# 		1 = stereo 8-bit PCM
# 		2 = mono 16-bit signed PCM
# 		3 = stereo 16-bit signed PCM
# 		4 = mono IMA ADPCM with block headers
# 		5 = stereo IMA ADPCM with block headers

# 16: uint16: block alignment in bytes (only appears if the format is ADPCM)

# BLOCK HEADER (length 4 * number of channels)
# 0: int16: IMA ADPCM predictor
# 2: uint8: IMA ADPCM step index
# (1 byte of zeros)

# then the sound data -- if the sound is ADPCM stereo, then the samples are nibble-interleaved, left channel first
