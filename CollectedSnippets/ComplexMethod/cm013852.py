def _detect_and_normalize_assert_statement(
    self: InstructionTranslatorBase,
    truth_fn: Callable[[object], bool],
    push: bool,
) -> bool:
    # Detect if this jump instruction is assert and normalize the assert
    # by pushing dummy error message when nothing is given.
    #
    # Python 3.9-3.13 assertion is in following format (minus small differences)
    # 18 POP_JUMP_IF_TRUE       28
    # 20 LOAD_ASSERTION_ERROR
    # 22 LOAD_CONST               3 ('Assert message') -> optional instruction
    # 24 CALL_FUNCTION            1                    -> optional instruction
    # 26 RAISE_VARARGS

    if (truth_fn is not operator.truth) or push:
        return False

    assert isinstance(self.instruction_pointer, int)
    current_instruction_pointer = self.instruction_pointer

    for with_msg in (False, True):
        assert_insts = get_assert_bytecode_sequence(with_msg)
        cur_insts = self.instructions[
            current_instruction_pointer : current_instruction_pointer
            + len(assert_insts)
        ]
        cur_insts = [inst.opname for inst in cur_insts]
        if cur_insts == assert_insts:
            if with_msg:
                load_const_idx = assert_insts.index("LOAD_CONST")
                error_msg = self.instructions[
                    current_instruction_pointer + load_const_idx
                ].argval
            else:
                error_msg = "assertion error"
            self.push(VariableTracker.build(self, error_msg))
            return True

    return False