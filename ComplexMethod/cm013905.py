def _get_or_create_code_info(self, code: types.CodeType) -> CodeInfo:
        """Get or create CodeInfo for a code object."""
        if code not in self._code_info:
            # Use dis.get_instructions directly to preserve original offsets.
            # cleaned_instructions strips EXTENDED_ARG and recalculates offsets,
            # which would cause mismatches with offsets reported by callbacks.
            instructions = [convert_instruction(i) for i in dis.get_instructions(code)]

            # In 3.11+, instructions have inline cache entries that occupy
            # bytecode space (e.g. BINARY_OP is 2 bytes + 2 bytes cache).
            # dis.get_instructions only reports the instruction start offset,
            # but sys.monitoring RAISE reports offsets within cache entries.
            # Map the full byte range of each instruction so lookups succeed.
            offset_to_inst: dict[int, Instruction] = {}
            offset_to_index: dict[int, int] = {}
            for i, inst in enumerate(instructions):
                if inst.offset is not None:
                    inst_size = instruction_size(inst)
                    for off in range(inst.offset, inst.offset + inst_size, 2):
                        offset_to_inst[off] = inst
                        offset_to_index[off] = i

            max_index = len(instructions) - 1 if instructions else 0
            max_offset = max(
                (inst.offset for inst in instructions if inst.offset is not None),
                default=0,
            )

            # Pre-populate breakpoints from BREAKPOINT_MARKER instructions
            programmatic_breakpoints: set[int] = {
                i
                for i, inst in enumerate(instructions)
                if self.is_programmatic_breakpoint(inst)
            }

            self._code_info[code] = CodeInfo(
                code=code,
                instructions=instructions,
                offset_to_inst=offset_to_inst,
                offset_to_index=offset_to_index,
                index_width=max(1, len(str(max_index))),
                offset_width=max(1, len(str(max_offset))),
                breakpoints=programmatic_breakpoints,
            )
        return self._code_info[code]