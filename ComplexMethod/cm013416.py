def type_repr(o: object) -> str:
            if o == ():
                # Empty tuple is used for empty tuple type annotation Tuple[()]
                return "()"

            typename = _type_repr(o)
            if isinstance(o, types.UnionType) and "|" in typename:
                # str | int
                args = [type_repr(arg) for arg in o.__args__]
                return "|".join(args)

            if origin_type := getattr(o, "__origin__", None):
                # list[...], typing.List[...], TensorType[...]

                if isinstance(o, typing._GenericAlias):  # type: ignore[attr-defined]
                    # This is a generic pre-PEP585 type, e.g. typing.List[torch.Tensor]
                    origin_type = _origin_type_map.get(origin_type, origin_type)

                origin_typename = add_global(_type_repr(origin_type), origin_type)

                if hasattr(o, "__args__") and o.__args__:
                    args = [type_repr(arg) for arg in o.__args__]
                    return f"{origin_typename}[{','.join(args)}]"
                else:
                    return origin_typename

            # Common case: this is a regular module name like 'foo.bar.baz'
            return add_global(typename, o)