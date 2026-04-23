def MAKE_FUNCTION(self, inst: Instruction) -> None:
        flags = inst.arg
        if sys.version_info < (3, 11):
            fn_name = self.pop()
        code = self.pop()
        if sys.version_info >= (3, 11):
            # MAKE_FUNCTION behavior actually changed in 3.11, see
            # https://github.com/python/cpython/pull/93189/
            assert hasattr(code.value, "co_qualname")  # type: ignore[attr-defined]
            fn_name = VariableTracker.build(self, code.value.co_qualname)  # type: ignore[attr-defined]
        defaults = None
        closure = None
        annotations = None
        kwdefaults = None

        if sys.version_info < (3, 13):
            # in 3.13, this is handled in SET_FUNCTION_ATTRIBUTE
            if flags is not None:
                if flags & 0x08:
                    closure = self.pop()
                if flags & 0x04:
                    annotations = self.pop()
                if flags & 0x02:
                    kwdefaults = self.pop()
                if flags & 0x01:
                    defaults = self.pop()

        fn = NestedUserFunctionVariable(
            fn_name,
            code,
            self.f_globals,
            defaults,
            kwdefaults,
            closure,
        )
        if annotations:
            assert isinstance(annotations, TupleVariable)
            # Convert the attribute to a dictionary before assigning it
            # https://github.com/python/cpython/blob/28fb13cb33d569720938258db68956b5f9c9eb40/Objects/funcobject.c#L574-L594
            items = annotations.items
            ann = ConstDictVariable(
                dict(zip(items[::2], items[1::2], strict=True)),
                mutation_type=ValueMutationNew(),
            )
            fn.get_dict_vt(self).setitem(  # pyrefly: ignore[bad-argument-type]
                "__annotations__", ann
            )
        self.push(fn)