def SEND(self, inst: Instruction) -> None:
        assert len(self.stack) >= 2
        val = self.pop()
        tos = self.stack[-1]
        if isinstance(tos, (IteratorVariable, LocalGeneratorObjectVariable)) or (
            isinstance(tos, UserDefinedObjectVariable)
            and isinstance(tos.value, collections.abc.Iterator)
        ):
            if val.is_constant_none():
                try:
                    val = tos.next_variable(self)  # type: ignore[arg-type]
                except (StopIteration, exc.ObservedUserStopIteration) as ex:
                    # To implement SEND, we have to look at the implementation
                    # when the iterator returns StopIteration. This translates to this code
                    # 3.11: https://github.com/python/cpython/blob/3.11/Python/ceval.c#L2613-L2619
                    # 3.12: https://github.com/python/cpython/blob/3.12/Python/bytecodes.c#L863-L866
                    # The implementation is different in 3.11 and 3.12. In 3.12, we rely
                    # on END_SEND to clean up. In 3.11, SEND does the cleanup as well.
                    if sys.version_info < (3, 12):
                        self.pop()  # Python 3.12 uses new opcode END_SEND
                    self.push(ConstantVariable.create(ex.value))
                    self.jump(inst)
                else:
                    self.push(val)
            else:
                # invoke send
                # Unreachable code - if you hit this, you are implementing generator support and have
                # lifted the `unimplemented("generator")` in frame conversion. This codepath handles
                # subgenerator and lines up with this line in Python 3.11
                # https://github.com/python/cpython/blob/3.11/Python/ceval.c#L2597
                unimplemented(
                    gb_type="Unreachable sub-generator code",
                    context="",
                    explanation="Should only be encountered while implementing generator support.",
                    hints=[],
                )
        else:
            unimplemented(
                gb_type="SEND with bad type",
                context=f"TOS type: {typestr(tos)}",
                explanation=f"Attempted to SEND with unsupported type {typestr(tos)}.",
                hints=[],
            )