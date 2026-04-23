def _remove_redundant_jumps(self) -> None:
        # Zero-length jumps can be introduced by _insert_continue_label and
        # _invert_hot_branches:
        for block in self._blocks():
            target = block.target
            if target is None:
                continue
            target = target.resolve()
            # Before:
            #    jmp FOO
            #    FOO:
            # After:
            #    FOO:
            if block.link and target is block.link.resolve():
                block.target = None
                block.fallthrough = True
                block.instructions.pop()
            # Before:
            #    branch  FOO:
            #    ...
            #    FOO:
            #    jump BAR
            # After:
            #    br cond BAR
            #    ...
            elif (
                len(target.instructions) == 1
                and target.instructions[0].kind == InstructionKind.JUMP
            ):
                assert target.target is not None
                assert target.target.label is not None
                if block.instructions[
                    -1
                ].kind == InstructionKind.SHORT_BRANCH and self._is_far_target(
                    target.target.label
                ):
                    continue
                block.target = target.target
                block.instructions[-1] = block.instructions[-1].update_target(
                    target.target.label
                )