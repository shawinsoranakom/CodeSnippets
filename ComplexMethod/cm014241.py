def _resolved_getattr_and_source(
        self, tx: "InstructionTranslator", name: str
    ) -> tuple[Any, AttrSource | None]:
        if not self.objvar:
            unimplemented(
                gb_type="1-arg super not implemented",
                context="",
                explanation=f"Dynamo failed to trace attribute `{name}` accessed "
                f"via `super()` (for type `{self.typevar}` and object `{self.objvar}`) "
                "because one-argument of super() is not supported.",
                hints=[
                    "Use two-argument super(type, object_or_type).",
                ],
            )
        assert self.objvar is not None
        search_type = self.typevar.as_python_constant()

        # The rest of this function does two things:
        #   - Walk the mro to find where the attribute comes from to be
        #     able to provide accurate source
        #   - Call the getattr to get the object

        # Find the class object, where the function lives.
        # When objvar is "self", use type(self), when objvar is "cls", use it as-is
        type_to_use = self.objvar.python_type()
        type_to_use_source: Source | None = (
            TypeSource(self.objvar.source) if self.objvar.source else None
        )
        if issubclass(type_to_use, type):
            type_to_use = self.objvar.value  # type: ignore[attr-defined]
            type_to_use_source = self.objvar.source

        source = None
        search_mro = type_to_use.__mro__

        try:
            start_index = search_mro.index(search_type) + 1
        except ValueError:
            # Corner case where the typevar is not in the mro of the objvar
            # https://github.com/python/cpython/blob/3.11/Objects/typeobject.c#L8843-L8844
            return getattr(super(search_type, type_to_use), name), None
        # Implemented based on https://github.com/python/cpython/blob/3.11/Objects/typeobject.c#L8812
        # super has its getattro implementation. The key point is that instead of calling getattr, it checks the
        # attribute in the class __dict__
        for index in range(start_index, len(search_mro)):
            # Dont call getattr, just check the __dict__ of the class
            if resolved_getattr := search_mro[index].__dict__.get(name, NO_SUCH_SUBOBJ):
                if resolved_getattr is not NO_SUCH_SUBOBJ:
                    # Equivalent of something like type(L['self']).__mro__[1].attr_name
                    if type_to_use_source:
                        source = AttrSource(
                            GetItemSource(TypeMROSource(type_to_use_source), index),
                            name,
                        )
                    return resolved_getattr, source

        unimplemented(
            gb_type="Unable to resolve super getattr",
            context="",
            explanation=f"Dynamo failed to trace attribute `{name}` accessed "
            f"via `super()` (for type `{self.typevar}` and object `{self.objvar}`) "
            "because the resolved attribute type is not supported.",
            hints=[
                "Ensure the attribute exists in the parent class.",
                "Check the arguments passed to `super()`.",
            ],
        )