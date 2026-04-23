def _emit_jit_symbol_table(self) -> None:
        got = len(self.data.body)
        for s, offset in self._jit_symbol_table.items():
            if s in self.symbols:
                value, addend = self.symbols[s]
                symbol = None
            else:
                value, symbol = symbol_to_value(s)
                addend = 0
            self.data.holes.append(
                Hole(got + offset, "R_X86_64_64", value, symbol, addend)
            )
            value_part = value.name if value is not HoleValue.ZERO else ""
            if value_part and not symbol and not addend:
                addend_part = ""
            else:
                signed = "+" if symbol is not None else ""
                addend_part = f"&{symbol}" if symbol else ""
                addend_part += f"{_signed(addend):{signed}#x}"
                if value_part:
                    value_part += "+"
            self.data.disassembly.append(
                f"{len(self.data.body):x}: {value_part}{addend_part}"
            )
            self.data.body.extend([0] * 8)