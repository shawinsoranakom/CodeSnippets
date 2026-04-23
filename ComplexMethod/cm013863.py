def WITH_EXCEPT_START(self, inst: Instruction) -> None:
        args: list[VariableTracker] = []
        if sys.version_info >= (3, 11):
            fn_loc = 4 if sys.version_info < (3, 14) else 5
            # At the top of the stack are 4 values:
            #    - TOP = exc_info()
            #    - SECOND = previous exception
            #    - THIRD: lasti of exception in exc_info()
            #    - FOURTH: the context.__exit__ bound method
            #    We call FOURTH(type(TOP), TOP, GetTraceback(TOP)).
            #    Then we push the __exit__ return value.
            # In Python 3.14+, there is a NULL placed between the context.__exit__ bound method and the lasti,
            # that is, fn is now the 5th from TOS.
            assert len(self.stack) >= fn_loc
            fn = self.stack[-fn_loc]
            val = self.stack[-1]
            assert self._isinstance_exception(val)
            typ = BuiltinVariable(val.exc_type)  # type: ignore[attr-defined, union-attr]
            tb = val.var_getattr(
                # pyrefly: ignore[bad-argument-type]
                self,
                "__traceback__",
            )
            if sys.version_info >= (3, 14):
                if not isinstance(self.stack[-4], NullVariable):
                    args.append(self.stack[-4])
        else:
            assert len(self.stack) >= 7
            fn = self.stack[-7]
            val = self.stack[-2]
            assert self._isinstance_exception(val)
            typ = BuiltinVariable(val.exc_type)  # type: ignore[attr-defined]

            tb = val.var_getattr(self, "__traceback__")

        args += [typ, val, tb]
        self.call_function(fn, args, {})