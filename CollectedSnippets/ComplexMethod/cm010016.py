def __init__(
        self,
        overloadpacket: "OpOverloadPacket",
        op: Callable[_P, _T],
        op_dk: Callable[Concatenate[DispatchKey, _P], _T],
        schema: torch._C.FunctionSchema,
        tags: list[Any],
    ) -> None:
        super().__init__()
        self._op = op
        self._op_dk = op_dk
        self._schema = schema
        self._overloadpacket = overloadpacket
        self._tags = tags
        self._overloadname = (
            "default" if schema.overload_name == "" else schema.overload_name
        )
        if tags:
            self._nondeterministic_seeded = torch.Tag.nondeterministic_seeded in tags
        self._name = self._schema.name
        if schema.overload_name:
            self._name += "." + schema.overload_name
        self.__name__ = f"{self._schema.name.split('::')[1]}.{self._overloadname}"
        self.__module__ = overloadpacket.__module__
        op.__module__ = overloadpacket.__module__
        self.__qualname__ = self._name
        self.__annotations__ = {}

        # If the OpOverload was constructed from a Library.def in Python.
        self._defined_in_python = self.__qualname__ in torch.library._defs

        # Logic replicated from aten/src/ATen/native/MathBitsFallback.h
        is_write = None
        for a in self._schema.arguments:  # pyrefly: ignore  # bad-assignment
            if a.alias_info is None:
                continue
            if is_write is None:
                is_write = a.alias_info.is_write
            else:
                # We will conservatively call mixed mutable/non-mutable
                # aliased inputs as NOT a view
                is_write = a.alias_info.is_write or is_write
        self.is_view = is_write is not None and not is_write