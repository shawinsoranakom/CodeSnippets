def parse_calculation(
        self, file_content: BytesIO, style: TaxonomyStyle
    ) -> dict[str, dict[str, Any]]:
        """Parse a calculation linkbase into a dictionary of element relationships.

        Calculation linkbases define how line items sum up, e.g.: Assets = CurrentAssets + NoncurrentAssets

        Parameters
        ----------
        file_content : BytesIO
            The content of the calculation linkbase file as a byte stream.
        style : TaxonomyStyle
            The style of taxonomy to determine how to find the linkbase (embedded vs standard).

        Returns
        -------
        dict[str, dict[str, Any]]
            A dictionary mapping child element_id to a dict with keys:
            - order: The order attribute from the arc (float)
            - weight: The weight attribute from the arc (float, usually 1 or -1)
            - parent_tag: The parent element_id that this child rolls up to
        """
        try:
            root = self._get_xml_root(file_content)

            if root is None:
                raise ValueError("Failed to parse XML calculation: root is None")

            # If embedded, find the linkbase inside annotations
            target_root = root
            if style == TaxonomyStyle.SEC_EMBEDDED and root.tag.endswith("schema"):
                found_lb = False
                for node in root.findall(".//link:linkbase", NS):
                    target_root = node
                    found_lb = True
                    break
                if not found_lb:
                    warnings.warn("No embedded linkbase found in XSD calculation.")
                    return {}

            # Build locator map: label -> element_id
            loc_map = {}
            for loc in target_root.findall(".//link:loc", NS):
                href = loc.get(f"{{{NS['xlink']}}}href")
                label = loc.get(f"{{{NS['xlink']}}}label")
                if href and "#" in href:
                    loc_map[label] = href.split("#")[1]

            # Parse calculation arcs
            calculations = {}
            for calc_link in target_root.findall(".//link:calculationLink", NS):
                for arc in calc_link.findall("link:calculationArc", NS):
                    parent_loc = arc.get(f"{{{NS['xlink']}}}from")
                    child_loc = arc.get(f"{{{NS['xlink']}}}to")
                    order = float(arc.get("order", "1.0"))
                    weight = float(arc.get("weight", "1"))

                    if parent_loc in loc_map and child_loc in loc_map:
                        child_id = loc_map[child_loc]
                        parent_id = loc_map[parent_loc]

                        calculations[child_id] = {
                            "order": order,
                            "weight": weight,
                            "parent_tag": parent_id,
                        }

            return calculations

        except Exception as e:
            raise OpenBBError(f"Failed to parse calculation linkbase: {e}") from e