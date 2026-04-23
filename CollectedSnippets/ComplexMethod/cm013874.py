def SET_FUNCTION_ATTRIBUTE(self, inst: Instruction) -> None:
        flags = inst.arg
        assert flags is not None
        fn = self.pop()
        assert isinstance(fn, NestedUserFunctionVariable)
        attr = self.pop()

        if flags & 0x10:
            assert sys.version_info >= (3, 14)

            # maybe use Format.VALUE_WITH_FAKE_GLOBALS instead?
            # https://docs.python.org/3/library/annotationlib.html#annotationlib.Format.VALUE_WITH_FAKE_GLOBALS
            attr = attr.call_function(self, [VariableTracker.build(self, 1)], {})
            fn.call_method(
                self,  # pyrefly: ignore[bad-argument-type]
                "__setattr__",
                [ConstantVariable.create("__annotations__"), attr],
                {},
            )
        elif flags & 0x08:
            fn.closure = attr
        elif flags & 0x04:
            assert isinstance(attr, TupleVariable)
            # Convert the attribute to a dictionary before assigning it
            # https://github.com/python/cpython/blob/28fb13cb33d569720938258db68956b5f9c9eb40/Objects/funcobject.c#L574-L594
            items = attr.items
            ann = ConstDictVariable(
                dict(zip(items[::2], items[1::2], strict=True)),
                mutation_type=ValueMutationNew(),
            )
            fn.get_dict_vt(self).setitem(  # pyrefly: ignore[bad-argument-type]
                "__annotations__", ann
            )
        elif flags & 0x02:
            fn.kwdefaults = attr
        elif flags & 0x01:
            fn.defaults = attr

        self.push(fn)