def replace_output(out):
        if not isinstance(spec, OutputSpec):
            raise AssertionError(f"expected OutputSpec, got {type(spec).__name__}")
        if spec.type == "user_output":
            arg = spec.user_output.arg
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
            elif arg.type in ("as_none", "as_bool", "as_int", "as_float", "as_string"):
                return
            else:
                raise AssertionError(f"Unknown input type: {arg}")
        elif spec.type == "loss_output":
            t = spec.loss_output.arg
            t.name = replace_table[t.name]
        elif spec.type == "buffer_mutation":
            t = spec.buffer_mutation.arg
            t.name = replace_table[t.name]
        elif spec.type == "parameter_mutation":
            t = spec.parameter_mutation.arg
            t.name = replace_table[t.name]
        elif spec.type == "gradient_to_parameter":
            t = spec.gradient_to_parameter.arg
            t.name = replace_table[t.name]
        elif spec.type == "gradient_to_user_input":
            g = spec.gradient_to_user_input
            g.arg.name = replace_table[g.arg.name]
            g.user_input_name = replace_table[g.user_input_name]
        elif spec.type == "user_input_mutation":
            u = spec.user_input_mutation
            u.arg.name = replace_table[u.arg.name]
            u.user_input_name = replace_table[u.user_input_name]
        elif spec.type == "token":
            tok = spec.token.arg
            tok.name = replace_table[tok.name]
        else:
            raise AssertionError(f"Unknown output type: {spec}")