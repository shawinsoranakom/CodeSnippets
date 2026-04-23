def parse_label_linkbase(
        self, file_content: BytesIO, style: TaxonomyStyle
    ) -> dict[str, Any]:
        """Update internal labels from a label linkbase file content.

        Parameters
        ----------
        file_content : BytesIO
            The content of the label linkbase file as a byte stream.
        style : TaxonomyStyle
            The style of taxonomy to determine how to find the linkbase (embedded vs standard).

        Returns
        -------
        dict[str, Any]
            A dictionary mapping element_id to a dict of label roles and their corresponding text.
        """
        try:
            root = self._get_xml_root(file_content)

            if root is None:
                raise ValueError("Failed to parse XML label linkbase: root is None")

            # If embedded, find the linkbase inside annotations
            target_root = root
            if style == TaxonomyStyle.SEC_EMBEDDED and root.tag.endswith("schema"):
                # Find annotation/appinfo/link:linkbase
                found_lb = False
                for node in root.findall(".//link:linkbase", NS):
                    target_root = node
                    found_lb = True
                    break
                if not found_lb:
                    warnings.warn("No embedded linkbase found in XSD labels.")
                    return {}

            loc_map = {}
            for loc in target_root.findall(".//link:loc", NS):
                href = loc.get(f"{{{NS['xlink']}}}href")
                label_key = loc.get(f"{{{NS['xlink']}}}label")
                if href and "#" in href:
                    loc_map[label_key] = href.split("#")[1]

            resource_map: dict[str | None, dict[str, str | None]] = {}
            for res in target_root.findall(".//link:label", NS):
                role = res.get(f"{{{NS['xlink']}}}role")
                # Simplify role to short name (e.g. terseLabel)
                role_short = role.split("/")[-1] if role else "label"
                label_key = res.get(f"{{{NS['xlink']}}}label")

                if label_key not in resource_map:
                    resource_map[label_key] = {}
                resource_map[label_key][role_short] = res.text

            new_labels: dict[str, dict[str, str | None]] = {}
            for arc in target_root.findall(".//link:labelArc", NS):
                from_loc = arc.get(f"{{{NS['xlink']}}}from")
                to_label = arc.get(f"{{{NS['xlink']}}}to")

                if from_loc in loc_map and to_label in resource_map:
                    element_id = loc_map[from_loc]
                    label_data = resource_map[to_label]

                    # Update standard labels store (simple string)
                    if "label" in label_data:
                        self.labels[element_id] = label_data["label"]  # type: ignore
                    elif "documentation" not in label_data and list(
                        label_data.values()
                    ):
                        self.labels[element_id] = list(label_data.values())[0]  # type: ignore

                    # Update documentation store
                    if "documentation" in label_data:
                        self.documentation[element_id] = label_data["documentation"]  # type: ignore

                    if element_id not in new_labels:
                        new_labels[element_id] = {}
                    new_labels[element_id].update(label_data)

            # Note: We don't update self.labels with the dictionary structure to avoid breaking
            # simple usage in XBRLManager, but the caller of this method gets the rich dict.
            return new_labels
        except Exception as e:
            raise OpenBBError(f"Failed to parse label linkbase: {e}") from e