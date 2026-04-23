def dump_type(t, level: int) -> tuple[str, str, str]:
            if getattr(t, "__name__", None) in cpp_enum_defs:
                return t.__name__, "int64_t", t.__name__
            elif t in _CPP_TYPE_MAP:
                return (t.__name__, _CPP_TYPE_MAP[t], _THRIFT_TYPE_MAP[t])
            elif isinstance(t, str):
                if t not in defs:
                    raise AssertionError(f"type {t} not in defs")
                if t in cpp_enum_defs:
                    raise AssertionError(f"type {t} unexpectedly in cpp_enum_defs")
                if "[" in t:
                    raise AssertionError(f"type {t} contains '[' which is not allowed")
                return t, f"ForwardRef<{t}>", t
            elif isinstance(t, ForwardRef):
                return (
                    t.__forward_arg__,
                    f"ForwardRef<{t.__forward_arg__}>",
                    t.__forward_arg__,
                )
            elif o := typing.get_origin(t):
                # Lemme know if there's a better way to do this.
                if o is list:
                    yaml_head, cpp_head, thrift_head, thrift_tail = (
                        "List",
                        "std::vector",
                        "list<",
                        ">",
                    )
                elif o is dict:
                    yaml_head, cpp_head, thrift_head, thrift_tail = (
                        "Dict",
                        "std::unordered_map",
                        "map<",
                        ">",
                    )
                elif o is Union or o is types.UnionType:
                    if level != 0:
                        raise AssertionError(
                            f"Optional is only supported at the top level, got level={level}"
                        )
                    args = typing.get_args(t)
                    if len(args) != 2 or args[1] is not type(None):
                        raise AssertionError(
                            f"expected Optional type with 2 args ending in None, got {args}"
                        )
                    yaml_type, cpp_type, thrift_type = dump_type(args[0], level + 1)
                    return (
                        f"Optional[{yaml_type}]",
                        f"std::optional<{cpp_type}>",
                        f"optional {thrift_type}",
                    )
                elif o is Annotated:
                    return dump_type(t.__origin__, level)
                else:
                    raise AssertionError(f"Type {t} is not supported in export schema.")
                yaml_arg_types, cpp_arg_types, thrift_arg_types = zip(
                    *[dump_type(x, level + 1) for x in typing.get_args(t)]
                )
                return (
                    (f"{yaml_head}[{', '.join(yaml_arg_types)}]"),
                    (f"{cpp_head}<{', '.join(cpp_arg_types)}>"),
                    f"{thrift_head}{', '.join(thrift_arg_types)}{thrift_tail}",
                )
            elif isinstance(t, type):
                return (t.__name__, t.__name__, t.__name__)
            else:
                raise AssertionError(f"Type {t} is not supported in export schema.")