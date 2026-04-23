def print_instruction_line(self, instr, mark_as_current):
        """Format instruction details for inclusion in disassembly output."""
        lineno_width = self.lineno_width
        offset_width = self.offset_width
        label_width = self.label_width

        new_source_line = (lineno_width > 0 and
                           instr.starts_line and
                           instr.offset > 0)
        if new_source_line:
            print(file=self.file)

        fields = []
        # Column: Source code locations information
        if lineno_width:
            if self.show_positions:
                # reporting positions instead of just line numbers
                if instr_positions := instr.positions:
                    if all(p is None for p in instr_positions):
                        positions_str = _NO_LINENO
                    else:
                        ps = tuple('?' if p is None else p for p in instr_positions)
                        positions_str = f"{ps[0]}:{ps[2]}-{ps[1]}:{ps[3]}"
                    fields.append(f'{positions_str:{lineno_width}}')
                else:
                    fields.append(' ' * lineno_width)
            else:
                if instr.starts_line:
                    lineno_fmt = "%%%dd" if instr.line_number is not None else "%%%ds"
                    lineno_fmt = lineno_fmt % lineno_width
                    lineno = _NO_LINENO if instr.line_number is None else instr.line_number
                    fields.append(lineno_fmt % lineno)
                else:
                    fields.append(' ' * lineno_width)
        # Column: Label
        if instr.label is not None:
            lbl = f"L{instr.label}:"
            fields.append(f"{lbl:>{label_width}}")
        else:
            fields.append(' ' * label_width)
        # Column: Instruction offset from start of code sequence
        if offset_width > 0:
            fields.append(f"{repr(instr.offset):>{offset_width}}  ")
        # Column: Current instruction indicator
        if mark_as_current:
            fields.append('-->')
        else:
            fields.append('   ')
        # Column: Opcode name
        fields.append(instr.opname.ljust(_OPNAME_WIDTH))
        # Column: Opcode argument
        if instr.arg is not None:
            # If opname is longer than _OPNAME_WIDTH, we allow it to overflow into
            # the space reserved for oparg. This results in fewer misaligned opargs
            # in the disassembly output.
            opname_excess = max(0, len(instr.opname) - _OPNAME_WIDTH)
            fields.append(repr(instr.arg).rjust(_OPARG_WIDTH - opname_excess))
            # Column: Opcode argument details
            if instr.argrepr:
                fields.append('(' + instr.argrepr + ')')
        print(' '.join(fields).rstrip(), file=self.file)