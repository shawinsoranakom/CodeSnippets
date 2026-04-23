def process_relocations(self, known_symbols: dict[str, int]) -> None:
        """Fix up all GOT and internal relocations for this stencil group."""
        for hole in self.code.holes.copy():
            if (
                hole.kind
                in {"R_AARCH64_CALL26", "R_AARCH64_JUMP26", "ARM64_RELOC_BRANCH26"}
                and hole.value is HoleValue.ZERO
                and hole.symbol not in self.symbols
            ):
                hole.func = "patch_aarch64_trampoline"
                hole.need_state = True
                assert hole.symbol is not None
                if hole.symbol in known_symbols:
                    ordinal = known_symbols[hole.symbol]
                else:
                    ordinal = len(known_symbols)
                    known_symbols[hole.symbol] = ordinal
                self._trampolines.add(ordinal)
                hole.addend = ordinal
                hole.symbol = None
            # x86_64 Darwin trampolines for external symbols
            elif (
                hole.kind == "X86_64_RELOC_BRANCH"
                and hole.value is HoleValue.ZERO
                and hole.symbol not in self.symbols
            ):
                hole.func = "patch_x86_64_trampoline"
                hole.need_state = True
                assert hole.symbol is not None
                if hole.symbol in known_symbols:
                    ordinal = known_symbols[hole.symbol]
                else:
                    ordinal = len(known_symbols)
                    known_symbols[hole.symbol] = ordinal
                self._trampolines.add(ordinal)
                hole.addend = ordinal
                hole.symbol = None
            elif (
                hole.kind in _AARCH64_GOT_RELOCATIONS | _X86_GOT_RELOCATIONS
                and hole.symbol
                and "_JIT_" not in hole.symbol
                and hole.value is HoleValue.GOT
            ):
                if hole.symbol in known_symbols:
                    ordinal = known_symbols[hole.symbol]
                else:
                    ordinal = len(known_symbols)
                    known_symbols[hole.symbol] = ordinal
                self._got_entries.add(ordinal)
        self.data.pad(8)
        for stencil in [self.code, self.data]:
            for hole in stencil.holes:
                if hole.value is HoleValue.GOT:
                    assert hole.symbol is not None
                    if "_JIT_" in hole.symbol:
                        # Relocations for local symbols
                        hole.value = HoleValue.DATA
                        hole.addend += self._jit_symbol_table_lookup(hole.symbol)
                    else:
                        _ordinal = known_symbols[hole.symbol]
                        _custom_value = f"got_symbol_address({_ordinal:#x}, state)"
                        if hole.kind in _X86_GOT_RELOCATIONS:
                            # When patching on x86, subtract the addend -4
                            # that is used to compute the 32 bit RIP relative
                            # displacement to the GOT entry
                            _custom_value = (
                                f"got_symbol_address({_ordinal:#x}, state) - 4"
                            )
                        hole.addend = _ordinal
                        hole.custom_value = _custom_value
                    hole.symbol = None
                elif hole.symbol in self.symbols:
                    hole.value, addend = self.symbols[hole.symbol]
                    hole.addend += addend
                    hole.symbol = None
                elif (
                    hole.kind in {"IMAGE_REL_AMD64_REL32"}
                    and hole.value is HoleValue.ZERO
                ):
                    raise ValueError(
                        f"Add PyAPI_FUNC(...) or PyAPI_DATA(...) to declaration of {hole.symbol}!"
                    )
        self._emit_jit_symbol_table()
        self._emit_global_offset_table()
        self.code.holes.sort(key=lambda hole: hole.offset)
        self.data.holes.sort(key=lambda hole: hole.offset)