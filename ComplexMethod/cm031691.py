def __post_init__(self) -> None:
        # Split the code into a linked list of basic blocks. A basic block is an
        # optional label, followed by zero or more non-instruction lines,
        # followed by zero or more instruction lines (only the last of which may
        # be a branch, jump, or return):
        self.text = self._preprocess(self.path.read_text())
        block = self._root
        for line in self.text.splitlines():
            # See if we need to start a new block:
            if match := self._re_label.match(line):
                # Label. New block:
                block.link = block = self._lookup_label(match["label"])
                block.noninstructions.append(line)
                continue
            if match := self.re_global.match(line):
                self.globals.add(match["label"])
                block.noninstructions.append(line)
                continue
            if self._re_noninstructions.match(line):
                if block.instructions:
                    # Non-instruction lines. New block:
                    block.link = block = _Block()
                block.noninstructions.append(line)
                continue
            if block.target or not block.fallthrough:
                # Current block ends with a branch, jump, or return. New block:
                block.link = block = _Block()
            inst = self._parse_instruction(line)
            block.instructions.append(inst)
            if inst.is_branch():
                # A block ending in a branch has a target and fallthrough:
                assert inst.target is not None
                block.target = self._lookup_label(inst.target)
                assert block.fallthrough
            elif inst.kind == InstructionKind.CALL:
                # A block ending in a call has a target and return point after call:
                assert inst.target is not None
                block.target = self._lookup_label(inst.target)
                assert block.fallthrough
            elif inst.kind == InstructionKind.JUMP:
                # A block ending in a jump has a target and no fallthrough:
                assert inst.target is not None
                block.target = self._lookup_label(inst.target)
                block.fallthrough = False
            elif inst.kind == InstructionKind.RETURN:
                # A block ending in a return has no target and fallthrough:
                assert not block.target
                block.fallthrough = False