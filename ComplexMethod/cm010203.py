def deserialize_sym_argument(self, sym_arg):
        if isinstance(sym_arg, SymIntArgument):
            if sym_arg.type == "as_int":
                return sym_arg.as_int
            elif sym_arg.type == "as_name":
                return self.serialized_name_to_node[sym_arg.as_name]
        elif isinstance(sym_arg, SymFloatArgument):
            if sym_arg.type == "as_float":
                return sym_arg.as_float
            elif sym_arg.type == "as_name":
                return self.serialized_name_to_node[sym_arg.as_name]
        elif isinstance(sym_arg, SymBoolArgument):
            if sym_arg.type == "as_bool":
                return sym_arg.as_bool
            elif sym_arg.type == "as_name":
                return self.serialized_name_to_node[sym_arg.as_name]
        raise SerializeError(f"Unknown symbolic argument type: {sym_arg}")