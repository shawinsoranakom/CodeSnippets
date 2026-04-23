def parse_schema_elements(self, file_content: BytesIO) -> list[XBRLNode]:
        """Extract elements from an XSD schema as a flat list of XBRLNode.

        This is used for reference/enumeration taxonomies (exch, country,
        currency, naics, sic, stpr, snj) that define flat element lists
        without any presentation linkbase hierarchy.

        Parameters
        ----------
        file_content : BytesIO
            The content of the XSD schema file.

        Returns
        -------
        list[XBRLNode]
            A flat list of XBRLNode objects (level=0, no children) for each
            non-abstract ``<xs:element>`` found, or all elements if every
            element is abstract.
        """
        try:
            root = self._get_xml_root(file_content)
            if root is None:
                raise ValueError("Failed to parse XML schema: root is None")

            nodes: list[XBRLNode] = []
            order_counter = 1.0

            for prefix in ["xs", "xsd"]:
                ns_uri = XSD_NS.get(prefix, "http://www.w3.org/2001/XMLSchema")
                for elem in root.findall(f"{{{ns_uri}}}element"):
                    elem_id = elem.get("id", "")
                    elem_name = elem.get("name", "")
                    if not elem_name:
                        continue

                    label = self.labels.get(elem_id, elem_name) or elem_name
                    doc = self.documentation.get(elem_id)
                    props = self.element_properties.get(elem_id, {})
                    elem_type = elem.get("type", "")
                    sub_group_raw = elem.get("substitutionGroup", "")
                    nodes.append(
                        XBRLNode(
                            element_id=elem_id,
                            label=label,
                            order=order_counter,
                            level=0,
                            parent_id=None,
                            preferred_label=None,
                            documentation=doc,
                            xbrl_type=props.get("xbrl_type")
                            or (elem_type.split(":")[-1] if elem_type else None),
                            period_type=props.get("period_type")
                            or elem.get(f"{{{XSD_NS['xbrli']}}}periodType"),
                            balance_type=props.get("balance_type")
                            or elem.get(f"{{{XSD_NS['xbrli']}}}balance"),
                            abstract=props.get(
                                "abstract", elem.get("abstract") == "true"
                            ),
                            substitution_group=props.get("substitution_group")
                            or (
                                sub_group_raw.split(":")[-1] if sub_group_raw else None
                            ),
                            nillable=props.get(
                                "nillable",
                                (
                                    elem.get("nillable") == "true"
                                    if elem.get("nillable")
                                    else None
                                ),
                            ),
                            children=[],
                        )
                    )
                    order_counter += 1.0

                if nodes:
                    break  # found elements with this prefix, skip the other

            return nodes
        except Exception as e:
            raise OpenBBError(f"Failed to parse schema elements: {e}") from e