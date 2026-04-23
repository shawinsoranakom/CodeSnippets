def _simple_type_parser(func, arg_name, arg_type):
            # Guess valid input to aten function based on type of argument
            if arg_type == "Tensor":
                return instance_gen()
            elif arg_type == "TensorList" or arg_type == "ITensorListRef":
                return [instance_gen(), instance_gen()]
            elif arg_type == "c10::List<::std::optional<Tensor>>":
                return [instance_gen(), instance_gen()]
            elif arg_type == "IntArrayRef" or arg_type == "SymIntArrayRef":
                size = arg.get("size", 2)
                if size == 1:
                    return 1
                else:
                    return [1] * size
            elif arg_type == "Scalar":
                return 3.5
            elif arg_type == "bool":
                return False
            elif arg_type == "Dimname":
                return ""
            elif arg_type == "DimnameList":
                return [""]
            elif arg_type.startswith("int"):
                return 0
            elif arg_type == "Stream":
                return torch.Stream()
            elif arg_type.startswith("float") or arg_type == "double":
                return 1.0
            elif arg_type in {"Generator", "MemoryFormat", "TensorOptions"}:
                return None
            elif arg_type == "ScalarType":
                return torch.float32
            elif arg_type == "c10::string_view":
                return ""
            elif arg_type in ("std::string_view", "::std::string_view"):
                return ""
            elif arg_type == "SymInt":
                # TODO: generate actual SymbolicInt
                return 1
            else:
                raise RuntimeError(
                    f"Unsupported argument type {arg_type} for {arg_name} of function {func}"
                )