def parse_schema(self, file_content: BytesIO) -> tuple[
        dict[str, dict[str, Any]],
        list[dict[str, Any]],
        Any | None,
        list[dict[str, str]],
    ]:
        """Parse a XBRL schema (.xsd) file.

        Parameters
        ----------
        file_content : BytesIO
            The content of the XSD file as a byte stream.

        Returns
        -------
        tuple[dict[str, dict[str, Any]], list[dict[str, Any]], Any | None, list[dict[str, str]]]
            - elements: dict mapping element_id -> {name, xbrl_type, xsi_nil, period_type, balance_type}
            - roles: list of role definitions with {name, short_name, document_number, group, sub_group, long_name}
            - embedded_linkbase: The embedded linkbase element if present (for labels), or None
            - imports: list of {namespace, schemaLocation} for imported taxonomies
        """
        try:
            root = self._get_xml_root(file_content)

            if root is None:
                raise ValueError("Failed to parse XML schema: root is None")

            elements: dict[str, dict[str, Any]] = {}
            roles: list[dict[str, Any]] = []
            embedded_linkbase = None
            imports: list[dict[str, str]] = []

            # Parse imports to identify external taxonomies
            for prefix in ["xsd", "xs"]:
                ns_uri = XSD_NS.get(prefix, "http://www.w3.org/2001/XMLSchema")
                for imp in root.findall(f"{{{ns_uri}}}import"):
                    namespace = imp.get("namespace", "")
                    schema_location = imp.get("schemaLocation", "")
                    if namespace and schema_location:
                        imports.append(
                            {"namespace": namespace, "schemaLocation": schema_location}
                        )

            # Parse elements - try both xsd: and xs: prefixes
            for prefix in ["xsd", "xs"]:
                for elem in root.findall(
                    f".//{{{XSD_NS.get(prefix, 'http://www.w3.org/2001/XMLSchema')}}}element"
                ):
                    elem_id = elem.get("id")
                    if not elem_id:
                        continue

                    elem_type = elem.get("type", "")
                    sub_group_raw = elem.get("substitutionGroup", "")
                    elements[elem_id] = {
                        "name": elem.get("name"),
                        "xbrl_type": elem_type.split(":")[-1] if elem_type else None,
                        "xsi_nil": elem.get("nillable"),
                        "period_type": elem.get(f"{{{XSD_NS['xbrli']}}}periodType"),
                        "balance_type": elem.get(f"{{{XSD_NS['xbrli']}}}balance"),
                        "abstract": elem.get("abstract") == "true",
                        "substitution_group": (
                            sub_group_raw.split(":")[-1] if sub_group_raw else None
                        ),
                    }

            # Parse role types from annotation/appinfo
            for prefix in ["xsd", "xs"]:
                ns_uri = XSD_NS.get(prefix, "http://www.w3.org/2001/XMLSchema")
                for role_type in root.findall(
                    f".//{{{ns_uri}}}annotation/{{{ns_uri}}}appinfo/{{{NS['link']}}}roleType"
                ):
                    role_id = role_type.get("id")

                    # Get definition text
                    definition_elem = role_type.find(f"{{{NS['link']}}}definition")
                    definition = (
                        definition_elem.text
                        if definition_elem is not None and definition_elem.text
                        else ""
                    )

                    # Parse definition format: "doc_num - type - subtype - name" or "doc_num - type - name"
                    parts = definition.split(" - ")
                    if len(parts) >= 3:
                        roles.append(
                            {
                                "name": role_id,
                                "short_name": parts[-1],
                                "document_number": parts[0],
                                "group": parts[1].lower() if len(parts) > 1 else "",
                                "sub_group": parts[2] if len(parts) > 3 else None,
                                "long_name": definition,
                            }
                        )

                # Check for embedded linkbase
                for linkbase in root.findall(
                    f".//{{{ns_uri}}}annotation/{{{ns_uri}}}appinfo/{{{NS['link']}}}linkbase"
                ):
                    embedded_linkbase = linkbase
                    break

            return elements, roles, embedded_linkbase, imports

        except Exception as e:
            raise OpenBBError(f"Failed to parse schema: {e}") from e