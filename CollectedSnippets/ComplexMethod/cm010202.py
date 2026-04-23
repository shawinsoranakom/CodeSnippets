def deserialize_input(self, inp: Argument) -> Any:
        value = inp.value
        typ_ = inp.type
        if typ_ == "as_none":
            # None should converted as None, but is encoded as bool in serialized
            # Convert serialized object to torch equivalent
            return None
        elif typ_ == "as_tensor":
            return self.serialized_name_to_node[inp.as_tensor.name]
        elif typ_ == "as_scalar_type":
            return _SERIALIZE_TO_TORCH_DTYPE[inp.as_scalar_type]
        elif typ_ == "as_memory_format":
            return _SERIALIZE_TO_TORCH_MEMORY_FORMAT[inp.as_memory_format]
        elif typ_ == "as_layout":
            return _SERIALIZE_TO_TORCH_LAYOUT[inp.as_layout]
        elif typ_ == "as_graph":
            if not isinstance(value, GraphArgument):
                raise AssertionError(
                    f"expected GraphArgument, got {type(value).__name__}"
                )
            with self.save_graph_module():
                self.deserialize_graph(value.graph)
                submodule = ep._create_graph_module_for_export(self.module, self.graph)
            self.module.register_module(value.name, submodule)
            return self.graph.create_node(
                "get_attr",
                value.name,
                name=value.name,
            )
        elif typ_ == "as_device":
            return deserialize_device(inp.as_device)
        elif typ_ == "as_int":
            return inp.as_int
        elif typ_ == "as_float":
            return inp.as_float
        elif typ_ == "as_bool":
            return inp.as_bool
        elif typ_ == "as_string":
            return inp.as_string
        elif typ_ == "as_complex":
            return complex(inp.as_complex.real, inp.as_complex.imag)
        elif typ_ == "as_sym_int":
            return self.deserialize_sym_argument(inp.as_sym_int)
        elif typ_ == "as_sym_float":
            return self.deserialize_sym_argument(inp.as_sym_float)
        elif typ_ == "as_sym_bool":
            return self.deserialize_sym_argument(inp.as_sym_bool)
        elif isinstance(value, dict):
            if typ_ == "as_string_to_argument":
                # Deserialize dict[str, Argument] recursively
                return {k: self.deserialize_input(v) for k, v in value.items()}
            else:
                raise SerializeError(f"Unknown dict type: {typ_}")
        elif isinstance(value, list):
            if len(value) == 0:
                return []
            elif typ_ == "as_tensors":
                result = [self.serialized_name_to_node[arg.name] for arg in value]
                return result
            elif typ_ in ("as_ints", "as_floats", "as_bools", "as_strings"):
                # convert from serialized.python.types.List to python list
                return list(value)
            elif typ_ == "as_int_lists":
                # Convert list of lists back to list of tuples for Triton grids
                return [tuple(dims) for dims in value]
            elif typ_ == "as_float_lists":
                return [list(floats) for floats in value]
            elif typ_ == "as_nested_tensors":
                # nested list of tensors (List[List[Tensor]])
                return [
                    [self.serialized_name_to_node[arg.name] for arg in inner_list]
                    for inner_list in value
                ]
            elif typ_ in ("as_sym_ints", "as_sym_bools", "as_sym_floats"):
                return [self.deserialize_sym_argument(arg) for arg in value]
            elif typ_ == "as_optional_tensors":

                def deserialize_optional_tensor_args(a):
                    if a.type == "as_none":
                        return None
                    elif a.type == "as_tensor":
                        return self.serialized_name_to_node[a.value.name]
                    else:
                        raise SerializeError(f"Unhandled argument {inp}")

                return list(map(deserialize_optional_tensor_args, value))
            else:
                raise SerializeError(f"Unhandled argument {inp}")
        elif typ_ == "as_custom_obj":
            if inp.as_custom_obj.name in self.serialized_name_to_node:
                # Custom object has been lifted as an input
                return self.serialized_name_to_node[inp.as_custom_obj.name]
            return self.constants[inp.as_custom_obj.name]
        elif typ_ == "as_operator":
            return self.deserialize_operator(inp.as_operator)
        else:
            raise SerializeError(f"Unhandled argument {inp}")