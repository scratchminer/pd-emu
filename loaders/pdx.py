from os import mkdir, sep as PATHSEP, walk
from os.path import abspath, basename, dirname, isdir, join as joinpath, normpath, splitext, relpath
from sys import argv

from loaders.pdfile import PDFile
from loaders.pda import PDAudioFile
from loaders.pdi import PDImageFile
from loaders.pds import PDStringsFile
from loaders.pdt import PDImageTableFile
from loaders.pdv import PDVideoFile
from loaders.pft import PDFontFile
from loaders.pdz import PDZipFile

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
			elif type(target) == PDZipFile: target.dump_files(joinpath(out_loc, "Source"))
			elif type(target) == StrayFile:
				non_pdfile = target.to_nonpdfile()
				with open(joinpath(out_loc, f"{filename}"), "wb") as f:
					f.write(non_pdfile)
			else:
				non_pdfile = target.to_nonpdfile()
				
				if type(non_pdfile) == list:
					for i in range(1, len(non_pdfile) + 1):
						framename = f"{splitext(filename)[0]}-table-{i}{target.NONPD_FILE_EXT}"
						with open(joinpath(out_loc, framename), "wb") as f:
							f.write(non_pdfile[i - 1])
				else:
					with open(joinpath(out_loc, f"{splitext(filename)[0]}{target.NONPD_FILE_EXT}"), "wb") as f:
						f.write(non_pdfile)
	
	def dump_files(self, out_loc):
		self._dump_dir(self.files, out_loc)

if __name__ == "__main__":
	if len(argv) == 1:
		print("To dump an application: python3 -m loaders.pdx [input PDX] [output directory]")
	else:
		filename = argv[1]
		if isdir(filename):
			if filename.endswith(PATHSEP): filename = filename[:-1]
			pdx_app = PDXApplication(filename)
			
			dump_loc = basename(filename)[:basename(filename).rindex(".")]
			if len(argv) > 2: dump_loc = argv[2]
			dump_loc = abspath(dump_loc)
						
			pdx_app.dump_files(dump_loc)
