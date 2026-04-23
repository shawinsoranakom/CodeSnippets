def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        if name == "__next__":
            return self.next_variable(tx)
        elif name == "__iter__":
            # iter(gen) returns itself
            return self
        elif name == "send":
            # Sends a value into the generator function. Returns the next value
            # yielded by the generator, or raises StopIteration if the generator
            # exits without yielding another value
            if self._is_generator_just_started() and len(args):
                # can't send non-None value to a just-started generator
                # Test: GeneratorCPythonTests.test_send_non_none_to_new_gen
                if not all(arg.is_constant_none() for arg in args):
                    raise_observed_exception(TypeError, tx)
            tracer = self.inline_tracer
            tracer.push_many(args)
            return self.next_variable(tx)
        elif name == "close":
            # * Raises a GeneratorExit at the point where the generator function was paused.
            # * If the generator function catches the exception and returns a
            # value, this value is returned from close() - Python 3.13+
            # * If the generator function is already closed, or raises GeneratorExit
            # (by not catching the exception), close() returns None.
            # * If the generator yields a value, a RuntimeError is raised.
            # * If the generator raises any other exception, it is propagated to the caller.
            # * If the generator has already exited due to an exception or normal
            # exit, close() returns None and has no other effect.

            # Return None if close is called on a just-started generator
            # See test GeneratorCloseCpythonTests::test_close_not_started

            tracer = self.inline_tracer
            if self._is_generator_just_started() or self._is_generator_exhausted():
                tracer.generator_exhausted = True
                return variables.ConstantVariable.create(None)

            # Raise GeneratorExit to see if user code catches it. Any other exception
            # is propagated to the parent frame.
            try:
                self._setup_exception(
                    tx, variables.ExceptionVariable(GeneratorExit, [])
                )
                # There's an extra block on Python 3.12+ to handle StopIteration
                # see: https://github.com/python/cpython/blob/8f93dd8a8f237b277abad20d566df90c5cbd7f1e/Objects/genobject.c#L394-L397
                #
                #   1           0 RETURN_GENERATOR
                #               2 POP_TOP
                #               4 RESUME                   0

                #   2           6 LOAD_CONST               1 (1)
                #               8 YIELD_VALUE              1
                #              10 RESUME                   1
                #              12 POP_TOP
                #              14 RETURN_CONST             0 (None)
                #         >>   16 CALL_INTRINSIC_1         3 (INTRINSIC_STOPITERATION_ERROR)
                #              18 RERAISE                  1
                # ExceptionTable:
                #   4 to 14 -> 16 [0] lasti
                if (
                    sys.version_info >= (3, 12)
                    and tracer.next_instruction.opname == "CALL_INTRINSIC_1"
                ):
                    tracer.generator_exhausted = True
                    return variables.ConstantVariable.create(None)
            except ObservedGeneratorExit:
                # If it doesn't catch, we just return None, as per the text above
                tracer.generator_exhausted = True
                return variables.ConstantVariable.create(None)

            try:
                # Raise RuntimeError if the generator yields any other value
                if self.next_variable(tx):
                    raise_observed_exception(RuntimeError, tx)
            except ObservedGeneratorExit:
                tracer.generator_exhausted = True
                return variables.ConstantVariable.create(None)
            except ObservedUserStopIteration:
                # In Python 3.13+, one can capture GeneratorExit and return a value
                # See test_generator.py::test_close_capture_GeneratorExit_return
                # https://discuss.python.org/t/let-generator-close-return-stopiteration-value/24786/26
                # https://github.com/python/cpython/pull/104771
                assert tracer.symbolic_result is not None
                return tracer.symbolic_result
        elif name == "throw":
            # * Raises an exception at the point where the generator was paused, and
            # returns the next value yielded by the generator.
            # * If the generator exits without yielding, raise StopIteration
            # * If the generator function does not catch the passed-in exception,
            # or raises a different exception, then that exception propagates to the caller.

            # Setup the exception table and jump target in case of try...finally
            tracer = self.inline_tracer
            try:
                # In Python 3.9, the exception is represented as a triple (typ, val, tb)
                # In such cases, we re-raise the exception object given to avoid
                # creating a new object, so that IS_OP works.
                # See: https://github.com/pytorch/pytorch/pull/146496
                self._setup_exception(tx, args[1] if len(args) == 3 else args[0])
            except ObservedException:  # noqa: TRY203
                # propagate the exception back to the parent caller
                raise

            retval = self.next_variable(tx)

            # The exception raised before is still active. We need to check the exception
            # table one more time to find the next target. But why? Let's walk
            # through an example and its generated bytecode: https://godbolt.org/z/ebdTbMv8M
            #
            #     z = 0
            #     def whoo():
            #         global z
            #         z = 0
            #         try:
            #             yield 1
            #         except ValueError:
            #             yield 2
            #         finally:
            #             z += 1
            #         z += 10
            #
            #     gen = whoo()
            #     next(gen)
            #     gen.throw(ValueError)
            #     print('z', z)  -> z = 1
            #
            #              ...
            #         >>   58 PUSH_EXC_INFO
            #
            #   8          60 LOAD_GLOBAL              2 (ValueError)
            #              70 CHECK_EXC_MATCH
            #              72 POP_JUMP_IF_FALSE        7 (to 88)
            #              74 POP_TOP
            #
            #   9          76 LOAD_CONST               3 (2)
            #              78 YIELD_VALUE              3      <------ ValueError is still active here
            #              80 RESUME                   1
            #              82 POP_TOP
            #              84 POP_EXCEPT
            #              86 jump_backward           34 (to 20)
            #              ...
            #
            #     ExceptionTable:
            #     4 to 8 -> 124 [0] lasti
            #     12 to 18 -> 58 [0]
            #     20 to 56 -> 124 [0] lasti
            #     58 to 82 -> 90 [1] lasti     <------ move to 90
            #     84 to 86 -> 96 [0]
            #     88 to 88 -> 90 [1] lasti
            #     90 to 94 -> 96 [0]
            #     96 to 116 -> 118 [1] lasti
            #     118 to 122 -> 124 [0] lasti
            #
            # In this scenario, a generator can yield after `throw()` is called. Even
            # after the exception is raised a few lines above, it remains active
            # within the `78 YIELD_VALUE` instruction. When the generator resumes
            # after the second yield on instruction `80 RESUME`, we cannot simply
            # return the control flow to the next instruction. Instead, one must
            # check the exception table (or equivalent) to find the next target
            # In this case, it says the instruction pointer must be moved to 90.
            #
            # Without this step, if we let the trace proceed to the next
            # instruction, it would follow the control flow where the exception
            # raised by `throw()` was handled and swallowed, potentially leading
            # to incorrect behavior.
            exc_type = type("__InternalThrowException", (Exception,), {})

            try:
                self._setup_exception(tx, variables.ExceptionVariable(exc_type, []))
                self.next_variable(tx)
            except get_dynamo_observed_exception(exc_type):
                # We should get back the exception raised before.
                pass
            else:
                raise_observed_exception(RuntimeError, tracer)
            return retval

        return super().call_method(tx, name, args, kwargs)