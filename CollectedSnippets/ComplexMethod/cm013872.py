def _call(self, inst: Instruction, call_kw: bool = False) -> None:
        # see https://docs.python.org/3.11/library/dis.html#opcode-CALL
        # for convention
        if call_kw:
            # TOS is kw_names for CALL_KW instruction
            assert sys.version_info >= (3, 13)
            kw_names = self.pop()
            assert isinstance(kw_names, TupleVariable) and kw_names.is_python_constant()
            kw_names = kw_names.as_python_constant()
        else:
            kw_names = self.kw_names.value if self.kw_names else ()

        assert inst.arg is not None
        contents = self.popn(inst.arg + 2)
        if sys.version_info >= (3, 13):
            # NULL and callable swapped
            fn = contents[0]
            args = [] if isinstance(contents[1], NullVariable) else [contents[1]]
        else:
            if isinstance(contents[0], NullVariable):
                fn = contents[1]
                # pyrefly: ignore [implicit-any]
                args = []
            else:
                fn = contents[0]
                args = [contents[1]]

        if kw_names:
            args = args + contents[2 : -len(kw_names)]

            kwargs_list = contents[-len(kw_names) :]

            kwargs = dict(zip(kw_names, kwargs_list))

            assert len(kwargs) == len(kw_names)
        else:
            args = args + contents[2:]
            # pyrefly: ignore [implicit-any]
            kwargs = {}

        try:
            # if call_function fails, need to set kw_names to None, otherwise
            # a subsequent call may have self.kw_names set to an old value
            self.call_function(fn, args, kwargs)
        finally:
            self.kw_names = None