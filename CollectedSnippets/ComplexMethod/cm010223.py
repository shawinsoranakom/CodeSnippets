def dump_cpp_value(v) -> str:
            if v is None:
                return "std::nullopt"
            elif v is True:
                return "true"
            elif v is False:
                return "false"
            elif v == {}:
                return "{}"
            elif v == []:
                return "{}"
            elif v == ():
                return "{}"
            elif isinstance(v, str):
                return f'"{v}"'
            else:
                raise AssertionError(
                    f"Default value {v} is not supported yet in export schema."
                )