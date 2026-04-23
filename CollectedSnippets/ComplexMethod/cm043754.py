def load_schema_element_properties(self, file_content: BytesIO) -> int:
        """Parse element properties from an XSD schema and store them.

        Extracts xbrl_type, period_type, balance_type, abstract,
        substitution_group, and nillable for every ``<xs:element>``
        and merges them into ``self.element_properties``.

        Parameters
        ----------
        file_content : BytesIO
            The content of the XSD schema file.

        Returns
        -------
        int
            The number of new element properties loaded.
        """
        try:
            root = self._get_xml_root(file_content)
            if root is None:
                return 0

            count = 0
            for prefix in ["xsd", "xs"]:
                ns_uri = XSD_NS.get(prefix, "http://www.w3.org/2001/XMLSchema")
                for elem in root.findall(f".//{{{ns_uri}}}element"):
                    elem_id = elem.get("id")
                    if not elem_id or elem_id in self.element_properties:
                        continue

                    elem_type = elem.get("type", "")
                    sub_group_raw = elem.get("substitutionGroup", "")
                    nillable_raw = elem.get("nillable")
                    self.element_properties[elem_id] = {
                        "xbrl_type": (elem_type.split(":")[-1] if elem_type else None),
                        "period_type": elem.get(f"{{{XSD_NS['xbrli']}}}periodType"),
                        "balance_type": elem.get(f"{{{XSD_NS['xbrli']}}}balance"),
                        "abstract": elem.get("abstract") == "true",
                        "substitution_group": (
                            sub_group_raw.split(":")[-1] if sub_group_raw else None
                        ),
                        "nillable": (
                            nillable_raw == "true" if nillable_raw is not None else None
                        ),
                    }
                    count += 1
            return count
        except Exception:  # pylint: disable=broad-except  # noqa: S112
            return 0