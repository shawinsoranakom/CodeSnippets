def _parse_summary(self):
        """Grab signature (if given) and summary"""
        if self._is_at_section():
            return

        # If several signatures present, take the last one
        while True:
            summary = self._doc.read_to_next_empty_line()
            summary_str = " ".join([s.strip() for s in summary]).strip()
            compiled = re.compile(r"^([\w., ]+=)?\s*[\w\.]+\(.*\)$")
            if compiled.match(summary_str):
                self["Signature"] = summary_str
                if not self._is_at_section():
                    continue
            break

        if summary is not None:
            self["Summary"] = summary

        if not self._is_at_section():
            self["Extended Summary"] = self._read_to_next_section()