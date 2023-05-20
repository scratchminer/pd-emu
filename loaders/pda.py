from io import BytesIO
from os.path import splitext
from sys import argv, byteorder as BYTEORDER
import wave

from loaders.pdfile import PDFile

MONO_8 = 0
STEREO_8 = 1
MONO_16 = 2
STEREO_16 = 3
MONO_ADPCM4 = 4
STEREO_ADPCM4 = 5
FORMAT_LENGTH = 6

IMA_INDEX_TABLE = [
	-1, -1, -1, -1, 2, 4, 6, 8,
	-1, -1, -1, -1, 2, 4, 6, 8
]
IMA_STEP_TABLE = [
	7, 8, 9, 10, 11, 12, 13, 14,
	16, 17, 19, 21, 23, 25, 28, 31,
	34, 37, 41, 45, 50, 55, 60, 66,
	73, 80, 88, 97, 107, 118, 130, 143,
	157, 173, 190, 209, 230, 253, 279, 307,
	337, 371, 408, 449, 494, 544, 598, 658,
	724, 796, 876, 963, 1060, 1166, 1282, 1411,
	1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024,
	3327, 3660, 4026, 4428, 4871, 5358, 5894, 6484,
	7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899,
	15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794,
	32767
]

# adapted from https://github.com/acida/pyima
class ADPCMDecoder:
	def __init__(self):
		self.predictor = 0
		self._step = 0
		self.step_index = 7
	
	def decode(self, nibble):
		# decode one sample from compressed nibble
		difference = 0
		
		if nibble & 4:
			difference += self._step
		if nibble & 2:
			difference += self._step >> 1
		if nibble & 1:
			difference += self._step >> 2
		difference += self._step >> 3
		if nibble & 8:
			difference = -difference
		
		self.predictor += difference
		
		if self.predictor > 32767:
			self.predictor = 32767
		elif self.predictor < -32767:
			self.predictor = - 32767
		
		self.step_index += IMA_INDEX_TABLE[nibble]
		if self.step_index < 0:
			self.step_index = 0
		elif self.step_index > 88:
			self.step_index = 88
		self._step = IMA_STEP_TABLE[self.step_index]
		
		return self.predictor
	
	def decode_block(self, block):
		result = bytes()
		self._step = IMA_STEP_TABLE[self.step_index]
		
		result += self.predictor.to_bytes(2, byteorder="little", signed=True)
		
		for i in range(len(block)):
			original_sample = block[i]
			first_sample = original_sample >> 4
			second_sample = original_sample & 0xf
			
			result += self.decode(first_sample).to_bytes(2, byteorder="little", signed=True)
			result += self.decode(second_sample).to_bytes(2, byteorder="little", signed=True)
		
		return result

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
		
		wavfile = wave.open(fh, "wb")
		
		wavfile.setnchannels(self.nchannels)
		wavfile.setsampwidth(self.sampwidth)
		wavfile.setframerate(self.framerate)
		
		data = bytes()
		stereo = (self.nchannels == 2)
		if self.fmt < MONO_ADPCM4: data = self.readbin()
		elif self.fmt < FORMAT_LENGTH:
			block_size = self.readu16()
			
			saved_pos = self.tell()
			self.handle.seek(0, 2)
			file_end = self.tell()
			self.seek(saved_pos)
			
			if stereo:
				decoder_left = ADPCMDecoder()
				decoder_right = ADPCMDecoder()
				
				def decode_stereo(sample):
					sample_left = sample >> 4
					sample_right = sample & 0xf
					
					return decoder_left.decode(sample_left).to_bytes(2, byteorder="little", signed=True) + decoder_right.decode(sample_right).to_bytes(2, byteorder="little", signed=True)
				
				for i in range(saved_pos, file_end, block_size):
					decoder_left.predictor = self.reads16()
					decoder_left.step_index = self.readu8()
					self.advance(1)
					
					decoder_right.predictor = self.reads16()
					decoder_right.step_index = self.readu8()
					self.advance(1)
					
					data += decoder_left.predictor.to_bytes(2, byteorder="little", signed=True)
					data += decoder_right.predictor.to_bytes(2, byteorder="little", signed=True)
					
					block = self.readbin(block_size - 8)
					data += b"".join(map(decode_stereo, tuple(block)))
					
			else:
				decoder = ADPCMDecoder()
				
				for i in range(saved_pos, file_end, block_size):
					decoder.predictor = self.reads16()
					decoder.step_index = self.readu8()
					self.advance(1)
					data += decoder.decode_block(self.readbin(block_size - 4))
			
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
	with open(f"{splitext(filename)[0]}{aud_file.NONPD_FILE_EXT}", "wb") as f:
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
