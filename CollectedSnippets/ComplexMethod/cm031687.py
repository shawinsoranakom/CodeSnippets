def _handle_section(
        self, section: _schema.COFFSection, group: _stencils.StencilGroup
    ) -> None:
        name = section["Name"]["Value"]
        if name == ".debug$S":
            # skip debug sections
            return
        flags = {flag["Name"] for flag in section["Characteristics"]["Flags"]}
        if "SectionData" in section:
            section_data_bytes = section["SectionData"]["Bytes"]
        else:
            # Zeroed BSS data, seen with printf debugging calls:
            section_data_bytes = [0] * section["RawDataSize"]
        if "IMAGE_SCN_MEM_EXECUTE" in flags:
            value = _stencils.HoleValue.CODE
            stencil = group.code
        elif "IMAGE_SCN_MEM_READ" in flags:
            value = _stencils.HoleValue.DATA
            stencil = group.data
        else:
            return
        base = len(stencil.body)
        group.symbols[section["Number"]] = value, base
        stencil.body.extend(section_data_bytes)
        for wrapped_symbol in section["Symbols"]:
            symbol = wrapped_symbol["Symbol"]
            offset = base + symbol["Value"]
            name = symbol["Name"]
            name = name.removeprefix(self.symbol_prefix)
            if name not in group.symbols:
                group.symbols[name] = value, offset
        for wrapped_relocation in section["Relocations"]:
            relocation = wrapped_relocation["Relocation"]
            hole = self._handle_relocation(base, relocation, stencil.body)
            stencil.holes.append(hole)