def _get_magic_functions(cls) -> List[str]:
            # ignore the handful of magic functions we cannot override without
            # breaking the Wrapper.
            ignore = ("__class__", "__dict__", "__getattribute__", "__getattr__")
            return [
                name
                for name in dir(cls)
                if name not in ignore and name.startswith("__")
            ]