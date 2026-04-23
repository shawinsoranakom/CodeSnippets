def replace_use(a):
        if a is None:
            return
        if isinstance(a, TensorArgument):
            a.name = name_table.get(a.name, a.name)
        elif isinstance(a, (SymIntArgument, SymFloatArgument)):
            if a.type == "as_name":
                a.as_name = name_table.get(a.as_name, a.as_name)
        elif isinstance(a, SymBoolArgument):
            if a.type == "as_name":
                a.as_name = name_table.get(a.as_name, a.as_name)
        elif isinstance(a, OptionalTensorArgument):
            if a.type == "as_tensor":
                a.as_tensor.name = name_table.get(a.as_tensor.name, a.as_tensor.name)
        elif isinstance(a, CustomObjArgument):
            a.name = name_table.get(a.name, a.name)
        else:
            raise AssertionError(f"Unknown argument type: {a}")