from lupa import LuaRuntime

# this function will go into the PDEmulator class
'''
def print_func(self, *args):
	if self.old_newline == "\n": print("[] ", end="")
	string_args = []
	for arg in args: string_args.append(RUNTIME.globals().tostring(arg))
	print(*string_args, end=self.newline, sep="\t")
	self.old_newline = self.newline
'''

RUNTIME = LuaRuntime(unpack_returned_tuples=True)
'''RUNTIME.set_global("print", self.print_func)'''