def _parse_instruction(self, line: str) -> Instruction:
        target = None
        reg = None
        if match := self._re_branch.match(line):
            target = match["target"]
            name = match["instruction"]
            if name in self._short_branches:
                kind = InstructionKind.SHORT_BRANCH
            else:
                kind = InstructionKind.LONG_BRANCH
        elif match := self._re_jump.match(line):
            target = match["target"]
            name = line[: -len(target)].strip()
            kind = InstructionKind.JUMP
        elif match := self._re_call.match(line):
            target = match["target"]
            name = line[: -len(target)].strip()
            kind = InstructionKind.CALL
        elif match := self._re_return.match(line):
            name = line
            kind = InstructionKind.RETURN
        elif match := self._re_small_const_1.match(line):
            target = match["value"]
            name = match["instruction"]
            reg = match["register"]
            kind = InstructionKind.SMALL_CONST_1
        elif match := self._re_small_const_2.match(line):
            target = match["value"]
            name = match["instruction"]
            reg = match["register"]
            kind = InstructionKind.SMALL_CONST_2
        elif match := self._re_small_const_mask.match(line):
            target = match["value"]
            name = match["instruction"]
            reg = match["register"]
            if reg.startswith("w"):
                reg = "x" + reg[1:]
            kind = InstructionKind.SMALL_CONST_MASK
        elif match := self._re_large_const_1.match(line):
            target = match["value"]
            name = match["instruction"]
            reg = match["register"]
            kind = InstructionKind.LARGE_CONST_1
        elif match := self._re_large_const_2.match(line):
            target = match["value"]
            name = match["instruction"]
            reg = match["register"]
            kind = InstructionKind.LARGE_CONST_2
        else:
            name, *_ = line.split(" ")
            kind = InstructionKind.OTHER
        return Instruction(kind, name, line, reg, target)