def get_base_type(  # pylint: disable=R0911 #  noqa:PLR0911
            t: Any,
        ) -> type:
            """Recursively find the base type for argparse."""
            origin = get_origin(t)
            args = get_args(t)

            if origin is Union or "types.UnionType" in str(type(t)):
                non_none_args = [a for a in args if a is not type(None)]
                if len(non_none_args) == 1:
                    return get_base_type(non_none_args[0])
                # For Union[A, B, C], check for bool first, then default to str
                if bool in non_none_args:
                    return bool
                # If we have multiple types including str, prefer str as it's most flexible
                if str in non_none_args:
                    return str
                # Otherwise, try to get the first concrete type
                for arg in non_none_args:
                    if arg not in (type(None), Any):
                        return get_base_type(arg)
                return str
            if origin is Literal:
                return type(args[0]) if args else str
            if origin is list:
                return get_base_type(args[0]) if args else Any  # type: ignore
            if t is Any:
                return str
            # Handle actual type objects (like datetime.date)
            if isinstance(t, type):
                return t
            return str