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
from logger import init_logging, get_logger

LOGGER = get_logger("loaders.pdx")

class StrayFile(PDFile):
	MAGIC = b""
	NONPD_FILE_EXT = ""
	
	def __init__(self, filename):
		LOGGER.info(f"Copying non-Playdate file {filename}...")
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
				is_pd_file = False
				for file_type in self.ALLOWED_FILE_TYPES:
					if branch.endswith(file_type.PD_FILE_EXT):
						is_pd_file = True
						workdir[branch] = file_type(joinpath(rootdir, branch))
						break
				if not is_pd_file: workdir[branch] = StrayFile(joinpath(rootdir, branch))
	
	def _dump_dir(self, root, out_loc, root_loc):
		try: mkdir(out_loc)
		except FileExistsError: pass
		
		for filename in root.keys():
			target = root[filename]
			if type(target) == dict: self._dump_dir(target, joinpath(out_loc, filename), root_loc)
			elif type(target) == PDZipFile: target.dump_files(root_loc)
			elif type(target) == StrayFile:
				non_pdfile = target.to_nonpdfile()
				with open(joinpath(out_loc, f"{filename}"), "wb") as f:
					f.write(non_pdfile)
			else:
				non_pdfile = target.to_nonpdfile()
				
				if type(target) == PDImageTableFile:
					if not target.is_matrix:
						for i in range(len(non_pdfile)):
							with open(joinpath(out_loc, f"{splitext(filename)[0]}-table-{i}{target.NONPD_FILE_EXT}"), "wb") as f:
								f.write(non_pdfile[i].to_nonpdfile())
					else:
						with open(joinpath(out_loc, f"{splitext(filename)[0]}-table-{target.image_table[0][0].stored_width}-{target.image_table[0][0].stored_height}{target.NONPD_FILE_EXT}"), "wb") as f:
							f.write(non_pdfile)
				else:
					with open(joinpath(out_loc, f"{splitext(filename)[0]}{target.NONPD_FILE_EXT}"), "wb") as f:
						f.write(non_pdfile)
	
	def dump_files(self, out_loc):
		self._dump_dir(self.files, out_loc, out_loc)

if __name__ == "__main__":
	init_logging()
	
	if len(argv) == 1:
		LOGGER.error("No argument specified")
		LOGGER.info("To dump an application: python3 -m loaders.pdx [input PDX] [output directory]")
	else:
		filename = argv[1]
		if isdir(filename):
			if filename.endswith(PATHSEP): filename = filename[:-1]
			pdx_app = PDXApplication(filename)
			
			dump_loc = basename(filename)[:basename(filename).rindex(".")]
			if len(argv) > 2: dump_loc = argv[2]
			dump_loc = abspath(dump_loc)
						
			pdx_app.dump_files(dump_loc)
