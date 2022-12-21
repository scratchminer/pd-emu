from os import mkdir, sep as PATHSEP, walk
from os.path import abspath, basename, dirname, isdir, join as joinpath, normpath, splitext, relpath
import io
from sys import argv

from pdfile import PDFile
from pda import PDAudioFile
from pdi import PDImageFile
from pds import PDStringsFile
from pdt import PDImageTableFile
from pdv import PDVideoFile
from pft import PDFontFile
from pdz import PDZipFile

class StrayFile(PDFile):
	MAGIC = b""
	NONPD_FILE_EXT = ""
	
	def __init__(self, filename):
		super().__init__(filename, skip_magic=True)
		self.seek(0)
	
	def to_nonpdfile(self):
		return self.data

class PDXApplication:
	ALLOWED_FILE_TYPES = [
		PDZipFile,
		PDAudioFile,
		PDImageFile,
		PDStringsFile,
		PDImageTableFile,
		PDVideoFile,
		PDFontFile
	]
	
	def __init__(self, filename):
		self.files = {}
		self.metadata = {}
		
		for rootdir, dirs, files in walk(filename):
			workdir = self.files
			root = relpath(rootdir, filename)
			if root != ".": 
				for subdir in root.split(PATHSEP): workdir = workdir[subdir]
			for subdir in dirs: workdir[subdir] = {}
			for branch in files:
				if root == ".": print(f"Loading {branch}...")
				else: print(f"Loading {joinpath(root, branch)}...")
				
				extension = splitext(branch)[1]
				is_pd_file = False
				for file_type in self.ALLOWED_FILE_TYPES:
					if extension == file_type.PD_FILE_EXT:
						is_pd_file = True
						workdir[branch] = file_type(joinpath(rootdir, branch))
						break
				if not is_pd_file: workdir[branch] = StrayFile(joinpath(rootdir, branch))
	
	def _dump_dir(self, root, out_loc):
		try: mkdir(out_loc)
		except FileExistsError: pass
		
		for filename in root.keys():			
			target = root[filename]
			if type(target) == dict: self._dump_dir(target, joinpath(out_loc, filename))
			elif type(target) == PDZipFile: target.dump_files(joinpath(out_loc, splitext(filename)[0]))
			else:
				non_pdfile = target.to_nonpdfile()
				
				if type(non_pdfile) == list:
					for i in range(len(non_pdfile)):
						framename = f"{splitext(filename)[0]}-frame{i}{target.NONPD_FILE_EXT}"
						with open(joinpath(out_loc, framename), "wb") as f:
							f.write(non_pdfile[i])
				else: 
					with open(joinpath(out_loc, f"{splitext(filename)[0]}{target.NONPD_FILE_EXT}"), "wb") as f:
						f.write(non_pdfile)
	
	def dump_files(self, out_loc):
		print("Dumping...")
		self._dump_dir(self.files, out_loc)

if __name__ == "__main__":
	if len(argv) == 1:
		print("To dump an application: python pdx.py [input PDX] [output directory]")
	else:
		filename = argv[1]
		if isdir(filename):
			if filename.endswith(PATHSEP): filename = filename[:-1]
			pdx_app = PDXApplication(filename)
			
			dump_loc = basename(filename)[:basename(filename).rindex(".")]
			if len(argv) > 2: dump_loc = argv[2]
			dump_loc = abspath(dump_loc)
						
			pdx_app.dump_files(dump_loc)
			