def _fixup_constants(self) -> None:
        for block in self._blocks():
            fixed: list[Instruction] = []
            small_const_part: dict[str, int | None] = {}
            small_const_whole: dict[str, str | None] = {}
            large_const_part: dict[str, int | None] = {}
            for inst in block.instructions:
                if inst.kind == InstructionKind.SMALL_CONST_1:
                    assert inst.register is not None
                    small_const_part[inst.register] = len(fixed)
                    small_const_whole[inst.register] = None
                    large_const_part[inst.register] = None
                    fixed.append(self._make_temp_label(inst.register))
                    fixed.append(inst)
                elif inst.kind == InstructionKind.SMALL_CONST_2:
                    assert inst.register is not None
                    index = small_const_part.get(inst.register)
                    small_const_part[inst.register] = None
                    if index is None:
                        fixed.append(inst)
                        continue
                    small_const_whole[inst.register] = self._fixup_small_constant_pair(
                        fixed, index, inst
                    )
                    small_const_part[inst.register] = None
                elif inst.kind == InstructionKind.SMALL_CONST_MASK:
                    assert inst.register is not None
                    reg = small_const_whole.get(inst.register)
                    if reg is not None:
                        self._fixup_mask(fixed, inst)
                    else:
                        fixed.append(inst)
                elif inst.kind == InstructionKind.LARGE_CONST_1:
                    assert inst.register is not None
                    small_const_part[inst.register] = None
                    small_const_whole[inst.register] = None
                    large_const_part[inst.register] = len(fixed)
                    fixed.append(self._make_temp_label())
                    fixed.append(inst)
                elif inst.kind == InstructionKind.LARGE_CONST_2:
                    assert inst.register is not None
                    small_const_part[inst.register] = None
                    small_const_whole[inst.register] = None
                    index = large_const_part.get(inst.register)
                    large_const_part[inst.register] = None
                    if index is None:
                        fixed.append(inst)
                        continue
                    self._fixup_large_constant_pair(fixed, index, inst)
                else:
                    for reg in small_const_part:
                        if self.may_use_reg(inst, reg):
                            small_const_part[reg] = None
                    for reg in small_const_whole:
                        if self.may_use_reg(inst, reg):
                            small_const_whole[reg] = None
                    for reg in small_const_part:
                        if self.may_use_reg(inst, reg):
                            large_const_part[reg] = None
                    fixed.append(inst)
            block.instructions = fixed