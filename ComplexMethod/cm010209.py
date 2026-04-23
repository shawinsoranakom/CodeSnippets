def rename_def(a):
        def _rename(arg_name, values):
            new_name = f"_{len(name_table)}"
            if arg_name in name_table:
                raise AssertionError(f"arg_name {arg_name!r} already in name_table")
            name_table[arg_name] = new_name
            if arg_name not in values:
                raise AssertionError(f"arg_name {arg_name!r} not in values")
            values[new_name] = values.pop(arg_name)
            return new_name

        if a is None:
            return
        if isinstance(a, TensorArgument):
            a.name = _rename(a.name, graph.tensor_values)
        elif isinstance(a, SymIntArgument):
            if a.type == "as_name":
                a.as_name = _rename(a.as_name, graph.sym_int_values)
        elif isinstance(a, SymFloatArgument):
            if a.type == "as_name":
                a.as_name = _rename(a.as_name, graph.sym_float_values)
        elif isinstance(a, SymBoolArgument):
            if a.type == "as_name":
                a.as_name = _rename(a.as_name, graph.sym_bool_values)
        elif isinstance(a, CustomObjArgument):
            a.name = _rename(a.name, graph.custom_obj_values)
        else:
            raise AssertionError(f"Unknown argument type: {a}")