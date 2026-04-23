def parse_reference_linkbase(self, file_content: BytesIO) -> int:
        """Parse reference links from an XSD and use them as fallback documentation.

        SEC taxonomies like CYD, ECD, OEF, SBS, SPAC, SRO, and FND
        publish ``referenceLink`` elements in their main XSD with
        regulatory citation data (Publisher, Name, Section, etc.) but
        no ``role/documentation`` labels.  This method extracts those
        references and formats them as compact citation strings, storing
        them in ``self.documentation`` for elements that don't already
        have documentation.

        Parameters
        ----------
        file_content : BytesIO
            The content of the XSD schema file.

        Returns
        -------
        int
            The number of new documentation entries added.
        """
        try:
            root = self._get_xml_root(file_content)
            if root is None:
                return 0

            ref_links = list(root.iter(f"{{{NS['link']}}}referenceLink"))
            if not ref_links:
                return 0

            # Build loc map (label → element_id)
            loc_map: dict[str, str] = {}
            for ref_link in ref_links:
                for loc in ref_link.findall("link:loc", NS):
                    label_key = loc.get(f"{{{NS['xlink']}}}label", "")
                    href = loc.get(f"{{{NS['xlink']}}}href", "")
                    if href and "#" in href:
                        loc_map[label_key] = href.split("#")[1]

            # Build resource map (label → list of citation parts)
            resource_map: dict[str, list[dict[str, str]]] = {}
            for ref_link in ref_links:
                for ref in ref_link.findall("link:reference", NS):
                    label_key = ref.get(f"{{{NS['xlink']}}}label", "")
                    parts: dict[str, str] = {}
                    for child in ref:
                        tag = (
                            child.tag.split("}")[-1] if "}" in child.tag else child.tag
                        )
                        if child.text:
                            parts[tag] = child.text.strip()
                    if parts:
                        resource_map.setdefault(label_key, []).append(parts)

            # Build arc map (element_id → resource labels)
            elem_refs: dict[str, list[dict[str, str]]] = {}
            for ref_link in ref_links:
                for arc in ref_link.findall("link:referenceArc", NS):
                    from_loc = arc.get(f"{{{NS['xlink']}}}from", "")
                    to_ref = arc.get(f"{{{NS['xlink']}}}to", "")
                    element_id = loc_map.get(from_loc)
                    ref_parts_list = resource_map.get(to_ref, [])
                    if element_id and ref_parts_list:
                        elem_refs.setdefault(element_id, []).extend(ref_parts_list)

            # Format citations and store as documentation fallback
            count = 0
            for element_id, refs in elem_refs.items():
                if element_id in self.documentation:
                    continue  # Don't overwrite real documentation

                citations: list[str] = []
                for parts in refs:
                    name = parts.get("Name", "")
                    section = parts.get("Section", "")
                    if not name:
                        continue
                    cite = name
                    if section:
                        cite += f" §{section}"
                    # Append subsection/paragraph/subparagraph
                    sub = parts.get("Subsection", "")
                    para = parts.get("Paragraph", "")
                    subpara = parts.get("Subparagraph", "")
                    suffix_parts = [p for p in [sub, para, subpara] if p]
                    if suffix_parts:
                        cite += "(" + ")(".join(suffix_parts) + ")"
                    citations.append(cite)

                if citations:
                    # Deduplicate while preserving order
                    seen: set[str] = set()
                    unique: list[str] = []
                    for c in citations:
                        if c not in seen:
                            seen.add(c)
                            unique.append(c)
                    self.documentation[element_id] = "Ref: " + "; ".join(unique)
                    count += 1

            return count
        except Exception:  # noqa: BLE001
            return 0