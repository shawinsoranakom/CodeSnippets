def get_choices(t: Any) -> tuple:
            """Recursively find the choices for argparse."""
            origin = get_origin(t)
            args = get_args(t)

            if origin is Union or "types.UnionType" in str(type(t)):
                non_none_args = [a for a in args if a is not type(None)]
                all_choices: list = []
                for arg in non_none_args:
                    all_choices.extend(get_choices(arg))
                return tuple(set(all_choices))
            if origin is Literal:
                return args
            if origin is list and args:
                return get_choices(args[0])
            return ()