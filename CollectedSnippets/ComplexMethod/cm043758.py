def _parse_units(self, root: Element) -> dict[str, str]:
        """Parse xbrli:unit definitions from an XBRL instance document.

        Handles both simple units (single measure) and compound units
        (divide with numerator/denominator).

        Parameters
        ----------
        root : ET.Element
            The root element of the parsed XBRL instance document.

        Returns
        -------
        dict[str, str]
            A dictionary mapping unit IDs to their resolved measure strings.
            Simple units: "iso4217:USD", "shares", "pure"
            Compound units: "iso4217:USD / shares"
        """
        xbrli_ns = "http://www.xbrl.org/2003/instance"
        units: dict[str, str] = {}

        for unit_elem in root.findall(f".//{{{xbrli_ns}}}unit"):
            unit_id = unit_elem.get("id")
            if not unit_id:
                continue

            # Simple unit: <measure>iso4217:USD</measure>
            measure = unit_elem.find(f"{{{xbrli_ns}}}measure")
            if measure is not None and measure.text:
                units[unit_id] = self._resolve_measure(measure.text)
                continue

            # Compound unit: <divide><unitNumerator><measure>...</unitDenominator>
            divide = unit_elem.find(f"{{{xbrli_ns}}}divide")
            if divide is not None:
                numerator = divide.find(f"{{{xbrli_ns}}}unitNumerator")
                denominator = divide.find(f"{{{xbrli_ns}}}unitDenominator")

                num_measures = []
                den_measures = []

                if numerator is not None:
                    for m in numerator.findall(f"{{{xbrli_ns}}}measure"):
                        if m.text:
                            num_measures.append(self._resolve_measure(m.text))
                if denominator is not None:
                    for m in denominator.findall(f"{{{xbrli_ns}}}measure"):
                        if m.text:
                            den_measures.append(self._resolve_measure(m.text))

                num_str = " * ".join(num_measures) if num_measures else "?"
                den_str = " * ".join(den_measures) if den_measures else "?"
                units[unit_id] = f"{num_str} / {den_str}"
                continue

            # Fallback: unknown structure, store the unit_id itself
            units[unit_id] = unit_id

        return units