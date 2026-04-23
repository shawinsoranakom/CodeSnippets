def _handle_section(
        self, section: _schema.ELFSection, group: _stencils.StencilGroup
    ) -> None:
        section_type = section["Type"]["Name"]
        flags = {flag["Name"] for flag in section["Flags"]["Flags"]}
        if section_type == "SHT_RELA":
            assert "SHF_INFO_LINK" in flags, flags
            assert not section["Symbols"]
            maybe_symbol = group.symbols.get(section["Info"])
            if maybe_symbol is None:
                # These are relocations for a section we're not emitting. Skip:
                return
            value, base = maybe_symbol
            if value is _stencils.HoleValue.CODE:
                stencil = group.code
            else:
                assert value is _stencils.HoleValue.DATA
                stencil = group.data
            for wrapped_relocation in section["Relocations"]:
                relocation = wrapped_relocation["Relocation"]
                hole = self._handle_relocation(base, relocation, stencil.body)
                stencil.holes.append(hole)
        elif section_type == "SHT_PROGBITS":
            if "SHF_ALLOC" not in flags:
                return
            if "SHF_EXECINSTR" in flags:
                value = _stencils.HoleValue.CODE
                stencil = group.code
            else:
                value = _stencils.HoleValue.DATA
                stencil = group.data
            group.symbols[section["Index"]] = value, len(stencil.body)
            for wrapped_symbol in section["Symbols"]:
                symbol = wrapped_symbol["Symbol"]
                offset = len(stencil.body) + symbol["Value"]
                name = symbol["Name"]["Name"]
                name = name.removeprefix(self.symbol_prefix)
                group.symbols[name] = value, offset
            stencil.body.extend(section["SectionData"]["Bytes"])
            assert not section["Relocations"]
        else:
            assert section_type in {
                "SHT_GROUP",
                "SHT_LLVM_ADDRSIG",
                "SHT_NOTE",
                "SHT_NULL",
                "SHT_STRTAB",
                "SHT_SYMTAB",
            }, section_type