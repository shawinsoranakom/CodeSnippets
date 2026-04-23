def _fixup_small_constant_pair(
        self, output: list[Instruction], label_index: int, inst: Instruction
    ) -> str | None:
        first = output[label_index + 1]
        reg = first.register
        if reg is None or inst.register != reg:
            output.append(
                Instruction(InstructionKind.OTHER, "", "# registers differ", None, None)
            )
            output.append(inst)
            return None
        assert first.target is not None
        if first.target != inst.target:
            output.append(
                Instruction(InstructionKind.OTHER, "", "# targets differ", None, None)
            )
            output.append(inst)
            return None
        if not self._both_registers_same(inst):
            output.append(
                Instruction(
                    InstructionKind.OTHER, "", "# not same register", None, None
                )
            )
            output.append(inst)
            return None
        pre, _ = first.text.split(first.name)
        output[label_index + 1] = Instruction(
            InstructionKind.OTHER,
            "movz",
            f"{pre}movz {reg}, 0",
            reg,
            None,
        )
        label_text = f"{self.const_reloc}16a_JIT_RELOCATION_CONST{first.target[:-3]}_JIT_RELOCATION_{self.label_index}:"
        self.label_index += 1
        output[label_index] = Instruction(
            InstructionKind.OTHER, "", label_text, None, None
        )
        assert first.target.endswith("16") or first.target.endswith("32")
        if first.target.endswith("32"):
            label_text = f"{self.const_reloc}16b_JIT_RELOCATION_CONST{first.target[:-3]}_JIT_RELOCATION_{self.label_index}:"
            self.label_index += 1
            output.append(
                Instruction(InstructionKind.OTHER, "", label_text, None, None)
            )
            pre, _ = inst.text.split(inst.name)
            output.append(
                Instruction(
                    InstructionKind.OTHER,
                    "movk",
                    f"{pre}movk {reg}, 0, lsl #16",
                    reg,
                    None,
                )
            )
        return reg