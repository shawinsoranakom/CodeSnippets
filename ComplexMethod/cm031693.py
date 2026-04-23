def _invert_hot_branches(self) -> None:
        for branch in self._blocks():
            link = branch.link
            if link is None:
                continue
            jump = link.resolve()
            # Before:
            #    je HOT
            #    jmp COLD
            # After:
            #    jne COLD
            #    jmp HOT
            if (
                # block ends with a branch to hot code...
                branch.target
                and branch.fallthrough
                and branch.target.hot
                # ...followed by a jump to cold code with no other predecessors:
                and jump.target
                and not jump.fallthrough
                and not jump.target.hot
                and len(jump.instructions) == 1
                and list(self._predecessors(jump)) == [branch]
            ):
                assert jump.target.label
                assert branch.target.label
                inverted = self._invert_branch(
                    branch.instructions[-1], jump.target.label
                )
                # Check to see if the branch can even be inverted:
                if inverted is None:
                    continue
                branch.instructions[-1] = inverted
                jump.instructions[-1] = jump.instructions[-1].update_target(
                    branch.target.label
                )
                branch.target, jump.target = jump.target, branch.target
                jump.hot = True