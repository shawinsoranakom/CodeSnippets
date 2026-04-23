def _parse(self):
        self._doc.reset()
        self._parse_summary()

        sections = list(self._read_sections())
        section_names = {section for section, content in sections}

        has_yields = "Yields" in section_names
        # We could do more tests, but we are not. Arbitrarily.
        if not has_yields and "Receives" in section_names:
            msg = "Docstring contains a Receives section but not Yields."
            raise ValueError(msg)

        for section, content in sections:
            if not section.startswith(".."):
                section = (s.capitalize() for s in section.split(" "))
                section = " ".join(section)
                if self.get(section):
                    self._error_location(
                        "The section %s appears twice in  %s"
                        % (section, "\n".join(self._doc._str))
                    )

            if section in ("Parameters", "Other Parameters", "Attributes", "Methods"):
                self[section] = self._parse_param_list(content)
            elif section in ("Returns", "Yields", "Raises", "Warns", "Receives"):
                self[section] = self._parse_param_list(
                    content, single_element_is_type=True
                )
            elif section.startswith(".. index::"):
                self["index"] = self._parse_index(section, content)
            elif section == "See Also":
                self["See Also"] = self._parse_see_also(content)
            else:
                self[section] = content