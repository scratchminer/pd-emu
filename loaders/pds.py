import json
from sys import argv

from pdfile import PDFile

class PDStringsFile(PDFile):
    
    MAGIC = b"Playdate STR"
    PD_FILE_EXT = ".pds"
    NONPD_FILE_EXT = ".json"

    def __init__(self, filename, skip_magic=False):
        super().__init__(filename, skip_magic)
        
        flags = self.readu32()
        compressed = bool(flags & 0x80000000)
        if compressed: self.advance(16)
        self.decompress(compressed)

        self.num_keys = self.readu32()
        offsets = [0x00000000]
        self.string_table = {}
        
        for i in range(self.num_keys - 1):
            offsets.append(self.readu32())
        header_end = self.tell()
        
        for i in range(len(offsets) - 1):
            self.seekrelto(header_end, offsets[i])
            k = self.readstr()
            v = self.readstr()
            self.string_table[k] = v
    
    def to_dict(self):
        return self.string_table

    def to_jsonfile(self):
        self.jsonfile = bytes(json.dumps(self.string_table, indent="\t"), "utf-8")
        return self.jsonfile

    def to_nonpdfile(self):
        return self.to_jsonfile()

if __name__ == "__main__":
    filename = argv[1]
    str_file = PDStringsFile(filename)
    with open(filename + str_file.NONPD_FILE_EXT, "wb") as f:
        f.write(str_file.to_jsonfile())
