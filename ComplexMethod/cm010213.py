def replace_input(spec):
        if not isinstance(spec, InputSpec):
            raise AssertionError(f"expected InputSpec, got {type(spec).__name__}")
        if spec.type == "user_input":
            arg = spec.user_input.arg
            if arg.type == "as_tensor":
                t = arg.as_tensor
                t.name = replace_table[t.name]
            elif arg.type == "as_sym_int":
                s = arg.as_sym_int
                if s.type == "as_name":
                    s.as_name = replace_table[s.as_name]
                elif s.type == "as_int":
                    pass
                else:
                    raise AssertionError(f"Unknown sym_int type: {s}")
            elif arg.type == "as_sym_float":
                f = arg.as_sym_float
                if f.type == "as_name":
                    f.as_name = replace_table[f.as_name]
                elif f.type == "as_float":
                    pass
                else:
                    raise AssertionError(f"Unknown sym_float type: {f}")
            elif arg.type in (
                "as_none",
                "as_bool",
                "as_int",
                "as_float",
                "as_string",
                "as_custom_obj",
            ):
                return
            else:
                raise AssertionError(f"Unknown input type: {arg}")
        elif spec.type == "parameter":
            t = spec.parameter.arg
            t.name = replace_table[t.name]
        elif spec.type == "buffer":
            t = spec.buffer.arg
            t.name = replace_table[t.name]
        elif spec.type == "tensor_constant":
            t = spec.tensor_constant.arg
            t.name = replace_table[t.name]
        elif spec.type == "custom_obj":
            t_custom_obj = spec.custom_obj.arg
            t_custom_obj.name = replace_table[t_custom_obj.name]
            return
        elif spec.type == "token":
            tok = spec.token.arg
            tok.name = replace_table[tok.name]
        elif spec.type == "constant_input":
            return
        else:
            raise AssertionError(f"Unknown input type: {spec}")