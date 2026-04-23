def __init__(self,
             # Positional args:
             name: str,
             py_name: str,
             function: Function,
             default: object = unspecified,
             *,  # Keyword only args:
             c_default: str | None = None,
             py_default: str | None = None,
             annotation: str | Literal[Sentinels.unspecified] = unspecified,
             unused: bool = False,
             **kwargs: Any
    ) -> None:
        self.name = libclinic.ensure_legal_c_identifier(name)
        self.py_name = py_name
        self.unused = unused
        self._includes: list[Include] = []

        if c_default:
            self.c_default = c_default
        if py_default:
            self.py_default = py_default

        if annotation is not unspecified:
            fail("The 'annotation' parameter is not currently permitted.")

        # Make sure not to set self.function until after converter_init() has been called.
        # This prevents you from caching information
        # about the function in converter_init().
        # (That breaks if we get cloned.)
        self.converter_init(**kwargs)

        if default is not unspecified:
            if self.default_type == ():
                conv_name = self.__class__.__name__.removesuffix('_converter')
                fail(f"A '{conv_name}' parameter cannot be marked optional.")
            if (default is not unknown
                and not isinstance(default, self.default_type)
            ):
                if isinstance(self.default_type, type):
                    types_str = self.default_type.__name__
                else:
                    names = [cls.__name__ for cls in self.default_type]
                    types_str = ', '.join(names)
                cls_name = self.__class__.__name__
                fail(f"{cls_name}: default value {default!r} for field "
                     f"{name!r} is not of type {types_str!r}")
            self.default = default

        if not self.c_default:
            if default is unspecified:
                if self.c_init_default:
                    self.c_default = self.c_init_default
            elif default is NULL:
                self.c_default = self.c_ignored_default or self.c_init_default
                if not self.c_default:
                    cls_name = self.__class__.__name__
                    fail(f"{cls_name}: c_default is required for "
                         f"default value NULL")
            else:
                assert default is not unknown
                self.c_default_init()
                if not self.c_default:
                    if default is None:
                        self.c_default = self.c_init_default
                        if not self.c_default:
                            cls_name = self.__class__.__name__
                            fail(f"{cls_name}: c_default is required for "
                                 f"default value None")
                    elif isinstance(default, str):
                        self.c_default = libclinic.c_str_repr(default)
                    elif isinstance(default, bytes):
                        self.c_default = libclinic.c_bytes_repr(default)
                    elif isinstance(default, (int, float)):
                        self.c_default = repr(default)
                    else:
                        cls_name = self.__class__.__name__
                        fail(f"{cls_name}: c_default is required for "
                             f"default value {default!r}")
                        fail(f"Unsupported default value {default!r}.")

        self.function = function