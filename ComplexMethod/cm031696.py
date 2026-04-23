def _fixup_external_labels(self) -> None:
        if self._supports_external_relocations:
            # Nothing to fix up
            return
        for index, block in enumerate(self._blocks()):
            if block.target and block.fallthrough:
                branch = block.instructions[-1]
                if branch.kind == InstructionKind.CALL:
                    continue
                assert branch.is_branch()
                target = branch.target
                assert target is not None
                reloc = self._branches[branch.name][1]
                if reloc is not None and self._is_far_target(target):
                    name = target[len(self.symbol_prefix) :]
                    label = f"{self.symbol_prefix}{reloc}_JIT_RELOCATION_{name}_JIT_RELOCATION_{index}:"
                    block.instructions[-1] = Instruction(
                        InstructionKind.OTHER, "", label, None, None
                    )
                    block.instructions.append(branch.update_target("0"))