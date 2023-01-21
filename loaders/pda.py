import io, wave
from sys import argv, byteorder as BYTEORDER

from loaders.pdfile import PDFile

MONO_8 = 0
STEREO_8 = 1
MONO_16 = 2
STEREO_16 = 3
MONO_ADPCM4 = 4
STEREO_ADPCM4 = 5
FORMAT_LENGTH = 6

# from the IMA ADPCM specification
ADPCM_STEP_TBL = [
	7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 
	19, 21, 23, 25, 28, 31, 34, 37, 41, 45, 
	50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 
	130, 143, 157, 173, 190, 209, 230, 253, 279, 307,
	337, 371, 408, 449, 494, 544, 598, 658, 724, 796,
	876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066, 
	2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871, 5358,
	5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899, 
	15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767
]

ADPCM_IDX_TBL = [-1, -1, -1, -1, 2, 4, 6, 8]

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
		fh = io.BytesIO()
		wavfile = wave.open(fh, "wb")
		
		self.nchannels = PDAudioFormat.get_nchannels(self.fmt)
		self.sampwidth = PDAudioFormat.get_sampwidth(self.fmt)
		
		wavfile.setnchannels(self.nchannels)
		wavfile.setsampwidth(self.sampwidth)
		wavfile.setframerate(self.framerate)
		
		data = bytes()
		stereo = (self.nchannels == 2)
		if self.fmt < MONO_ADPCM4: data = self.readbin(-1)
		elif self.fmt < FORMAT_LENGTH:
			block_len = self.readu16()
			
			done = False
			while not done:
				by = []
				if self.is_eof(): break
				
				predictor = []
				step_idx = []
				for i in range(self.nchannels):
					predictor.append(self.reads16())
					step_idx.append(self.readu8())
					self.advance(1)
				
				# Because Python's audioop is scheduled for removal, I recreated audioop.adpcm2lin in Python
				
				for i in range(2 * block_len - (16 if stereo else 8)):
					if i % 2 == 0:
						if self.is_eof():
							done = True
							break
						b = self.readu8()
						by = [b >> 4, b & 0xf]
					in_val = by[i % 2]
					
					ny = (i % 2) if stereo else 0
					
					step = ADPCM_STEP_TBL[step_idx[ny]]
					
					step_idx[ny] += ADPCM_IDX_TBL[in_val & 0x7]
					if step_idx[ny] < 0: step_idx[ny] = 0
					if step_idx[ny] >= len(ADPCM_STEP_TBL): step_idx[ny] = len(ADPCM_STEP_TBL) - 1
					
					delta = step >> 3
					if in_val & 0x1: delta += (step >> 2)
					if in_val & 0x2: delta += (step >> 1)
					if in_val & 0x4: delta += step
					if in_val & 0x8: 
						predictor[ny] -= delta
					else: 
						predictor[ny] += delta
					
					if predictor[ny] < -32768: predictor[ny] = -32768
					if predictor[ny] > 32767: predictor[ny] = 32767
					
					data += predictor[ny].to_bytes(2, byteorder=BYTEORDER, signed=True)
		
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

# 16: uint16: maximum block length in samples, plus the block header's length in bytes (only appears if the format is ADPCM)

# BLOCK HEADER (length 4 * number of channels)
# 0: int16: IMA ADPCM predictor
# 2: uint8: IMA ADPCM step index
# (1 byte of zeros)

# then the sound data -- if the sound is stereo, then the samples are nibble-interleaved, left channel first
