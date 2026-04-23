def get_name(a) -> str | None:
            if a is None:
                return None
            if isinstance(a, TensorArgument):
                return a.name
            elif isinstance(a, (SymIntArgument, SymBoolArgument, SymFloatArgument)):
                if a.type == "as_name":
                    return a.as_name
                elif a.type in ("as_int", "as_bool", "as_float"):
                    return None
                else:
                    raise AssertionError(f"Unknown argument type: {a}")
            elif isinstance(a, OptionalTensorArgument):
                if a.type == "as_tensor":
                    return a.as_tensor.name
                elif a.type == "as_none":
                    return None
                else:
                    raise AssertionError(f"Unknown optional tensor type: {a}")
            elif isinstance(a, CustomObjArgument):
                return a.name
            else:
                raise AssertionError(f"Unknown argument type: {a}")