def check_if_exc_matches(self) -> bool:
        assert len(self.stack) >= 2
        expected_exc_types = self.pop()
        if sys.version_info >= (3, 11):
            # CHECK_EXC_MATCH (which is used from 3.11 onwards) does not pop.
            # This is the description from the disassembly doc
            #
            # Performs exception matching for ``except``. Tests whether the ``STACK[-2]``
            # is an exception matching ``STACK[-1]``. Pops ``STACK[-1]`` and pushes the boolean
            # result of the test.
            exc_instance = self.stack[-1]
        else:
            # This is used prior to 3.11 via opcode JUMP_IF_NOT_EXC_MATCH
            # There is no documentation but here is the code pointer that does 2 pops
            # https://github.com/python/cpython/blob/3.10/Python/ceval.c#L3650-L3665
            exc_instance = self.stack.pop()

        # Users can check exception in 3 ways
        # 1) except NotImplementedError --> BuiltinVariable
        # 2) except CustomException --> UserDefinedExceptionClassVariable
        # 3) except (NotImplementedError, AttributeError) -> TupleVariable

        if not isinstance(
            expected_exc_types,
            (
                BuiltinVariable,
                TupleVariable,
                UserDefinedExceptionClassVariable,
                UserDefinedExceptionObjectVariable,
            ),
        ):
            unimplemented(
                gb_type="Exception with bad expected type",
                context=str(expected_exc_types),
                explanation=f"`except ...` has unsupported type {expected_exc_types}.",
                hints=[*graph_break_hints.USER_ERROR],
            )

        if sys.version_info >= (3, 11):
            if not self._isinstance_exception(exc_instance):
                unimplemented(
                    gb_type="Caught non-Exception value",
                    context=str(exc_instance),
                    explanation=f"Except expects to receive an object of Exception type but received {exc_instance}.",
                    hints=[*graph_break_hints.USER_ERROR],
                )

        if isinstance(expected_exc_types, TupleVariable):
            expected_types = expected_exc_types.items
        else:
            expected_types = [
                expected_exc_types,
            ]

        for expected_type in expected_types:
            if not isinstance(
                expected_type,
                (
                    BuiltinVariable,
                    UserDefinedExceptionObjectVariable,
                    UserDefinedExceptionClassVariable,
                ),
            ):
                unimplemented(
                    gb_type="Exception with non-type expectation",
                    context=str(expected_type),
                    explanation=f"`except ...` expects a non-type: {expected_type}.",
                    hints=[*graph_break_hints.USER_ERROR],
                )
            if self._isinstance_exception(exc_instance) and issubclass(
                exc_instance.exc_type,  # type: ignore[union-attr]
                expected_type.fn,  # type: ignore[attr-defined]
            ):
                return True
            elif isinstance(exc_instance, variables.BuiltinVariable) and issubclass(
                exc_instance.fn,
                # pyrefly: ignore [invalid-argument]
                expected_type.fn,
            ):
                return True

        return False