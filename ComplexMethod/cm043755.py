def parse_presentation(
        self, file_content: BytesIO, style: TaxonomyStyle
    ) -> list[XBRLNode]:
        """Parse a presentation linkbase into a hierarchical tree.

        Parameters
        ----------
        file_content : BytesIO
            The content of the presentation linkbase file as a byte stream.
        style : TaxonomyStyle
            The style of taxonomy to determine how to find the linkbase (embedded vs standard).

        Returns
        -------
        list[XBRLNode]
            A list of root XBRLNode objects representing the hierarchical structure of the presentation.
        """
        try:
            root = self._get_xml_root(file_content)

            if root is None:
                raise ValueError("Failed to parse XML presentation: root is None")

            # If embedded, find the linkbase inside annotations
            target_root = root
            if style == TaxonomyStyle.SEC_EMBEDDED and root.tag.endswith("schema"):
                found_lb = False
                for node in root.findall(".//link:linkbase", NS):
                    target_root = node
                    found_lb = True
                    break
                if not found_lb:
                    warnings.warn("No embedded linkbase found in XSD presentation.")
                    return []

            loc_map = {}
            for loc in target_root.findall(".//link:loc", NS):
                href = loc.get(f"{{{NS['xlink']}}}href")
                label = loc.get(f"{{{NS['xlink']}}}label")
                if href and "#" in href:
                    # SEC locators often point to local files, e.g., "dei-2024.xsd#element"
                    # We just want "element"
                    loc_map[label] = href.split("#")[1]

            relationships = []
            for arc in target_root.findall(".//link:presentationArc", NS):
                parent_loc = arc.get(f"{{{NS['xlink']}}}from")
                child_loc = arc.get(f"{{{NS['xlink']}}}to")
                order = float(arc.get("order", "1.0"))
                preferred_label = arc.get("preferredLabel")

                if parent_loc in loc_map and child_loc in loc_map:
                    relationships.append(
                        {
                            "parent": loc_map[parent_loc],
                            "child": loc_map[child_loc],
                            "order": order,
                            "preferred_label": preferred_label,
                        }
                    )

            # Build Tree
            all_children = set(r["child"] for r in relationships)
            all_parents = set(r["parent"] for r in relationships)
            roots = list(all_parents - all_children)

            def build_node(element_id, level=0, parent_id=None, preferred_label=None):
                """Recursively build a node and its children."""
                label = self.labels.get(element_id, element_id) or element_id
                doc = self.documentation.get(element_id)
                props = self.element_properties.get(element_id, {})
                node = XBRLNode(
                    element_id=element_id,
                    label=label,
                    order=0,
                    level=level,
                    parent_id=parent_id,
                    preferred_label=preferred_label,
                    documentation=doc,
                    xbrl_type=props.get("xbrl_type"),
                    period_type=props.get("period_type"),
                    balance_type=props.get("balance_type"),
                    abstract=props.get("abstract", False),
                    substitution_group=props.get("substitution_group"),
                    nillable=props.get("nillable"),
                    children=[],
                )

                my_children_rels = [
                    r for r in relationships if r["parent"] == element_id
                ]
                my_children_rels.sort(key=lambda x: float(x["order"]))  # type: ignore

                for rel in my_children_rels:
                    child_node = build_node(
                        rel["child"],
                        level + 1,
                        element_id,
                        rel["preferred_label"],
                    )
                    child_node.order = rel["order"]
                    node.children.append(child_node)

                return node

            return [build_node(r) for r in roots]

        except Exception as e:
            raise OpenBBError(f"Failed to parse presentation linkbase: {e}") from e