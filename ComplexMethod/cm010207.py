def _get_argument(a: Argument):
        if a.type == "as_none":
            return None
        elif a.type == "as_tensor":
            return a.as_tensor
        elif a.type == "as_tensors":
            return a.as_tensors
        elif a.type == "as_int":
            return None
        elif a.type == "as_ints":
            return None
        elif a.type == "as_float":
            return None
        elif a.type == "as_floats":
            return None
        elif a.type == "as_string":
            return None
        elif a.type == "as_strings":
            return None
        elif a.type == "as_complex":
            return None
        elif a.type == "as_sym_int":
            return a.as_sym_int
        elif a.type == "as_sym_ints":
            return a.as_sym_ints
        elif a.type == "as_sym_float":
            return a.as_sym_float
        elif a.type == "as_sym_floats":
            return a.as_sym_floats
        elif a.type == "as_scalar_type":
            return None
        elif a.type == "as_memory_format":
            return None
        elif a.type == "as_layout":
            return None
        elif a.type == "as_device":
            return None
        elif a.type == "as_bool":
            return None
        elif a.type == "as_bools":
            return None
        elif a.type == "as_sym_bool":
            return a.as_sym_bool
        elif a.type == "as_sym_bools":
            return a.as_sym_bools
        elif a.type == "as_graph":
            return None
        elif a.type == "as_optional_tensors":
            return a.as_optional_tensors
        elif a.type == "as_custom_obj":
            return a.as_custom_obj
        elif a.type == "as_operator":
            return None
        elif a.type == "as_int_lists":
            return None
        elif a.type == "as_float_lists":
            return None
        elif a.type == "as_string_to_argument":
            return None
        elif a.type == "as_nested_tensors":
            return a.as_nested_tensors
        else:
            raise AssertionError(f"Unknown input type to the ExportedProgram: {a}")