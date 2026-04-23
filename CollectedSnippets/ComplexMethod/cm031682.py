def convert_labels_to_relocations(self) -> None:
        holes_by_offset: dict[int, Hole] = {}
        first_in_pair: dict[str, Hole] = {}
        for hole in self.code.holes:
            holes_by_offset[hole.offset] = hole
        for name, hole_plus in self.symbols.items():
            if isinstance(name, str) and "_JIT_RELOCATION_" in name:
                _, offset = hole_plus
                reloc, target, _ = name.split("_JIT_RELOCATION_")
                value, symbol = symbol_to_value(target)
                hole = Hole(
                    int(offset), typing.cast(_schema.HoleKind, reloc), value, symbol, 0
                )
                self.code.holes.append(hole)
            elif isinstance(name, str) and "_JIT_PAIR_" in name:
                _, offset = hole_plus
                reloc, target, index = name.split("_JIT_PAIR_")
                if offset in holes_by_offset:
                    hole = holes_by_offset[offset]
                    if "33a" in reloc:
                        first_in_pair[index] = hole
                    elif "33b" in reloc and index in first_in_pair:
                        first = first_in_pair[index]
                        hole.fold(first)