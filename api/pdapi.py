from lupa import LuaRuntime

RUNTIME = LuaRuntime(register_builtins=False, register_eval=False, attribute_filter=_filter, unpack_returned_tuples=True)

