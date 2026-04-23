def _create_synthetic_groups_for_shared_prefixes(
        self, indicators: list[dict]
    ) -> list[dict]:
        """
        Create synthetic group nodes for IRFCL siblings with shared label patterns.

        For IRFCL path-encoded labels like:
        - "Up to 1 month, Long positions"
        - "More than 1 and up to 3 months, Long positions"

        This creates a parent group "Long positions" and re-parents the children
        with simplified labels ("Up to 1 month", etc.).

        Also handles shared prefixes like "Options in foreign currencies...".
        """
        # pylint: disable=import-outside-toplevel
        import re
        from collections import defaultdict

        # These are specific to IRFCL memo items structure
        IRFCL_PATH_PATTERNS = [  # pylint: disable=C0103
            "Options in foreign currencies",
            "Up to 1 month",
            "More than 1 and up to",
            "More than 3 months",
            "In-the-money",
            "Long positions",
            "Short positions",
        ]

        def is_irfcl_path_label(label: str) -> bool:
            """Check if label contains IRFCL path patterns."""
            return any(
                pattern.lower() in label.lower() for pattern in IRFCL_PATH_PATTERNS
            )

        # Group indicators by parent_id
        by_parent: dict[str | None, list[dict]] = defaultdict(list)
        for ind in indicators:
            by_parent[ind.get("parent_id")].append(ind)

        # Track new synthetic groups
        synthetic_groups: list[dict] = []

        # For each parent, check if children share a common prefix OR suffix
        for parent_id, children in by_parent.items():
            # Only process if multiple children with comma-separated labels
            # and they have IRFCL-specific path patterns (time periods, positions, options)
            path_children = [
                c
                for c in children
                if ", " in c.get("label", "")
                and c.get("id")
                and is_irfcl_path_label(c.get("label", ""))
            ]
            if len(path_children) < 2:
                continue

            # Find common prefix among path_children labels
            labels = [c["label"] for c in path_children]
            split_labels = [lbl.split(", ") for lbl in labels]
            if not all(split_labels):
                continue

            # Find how many leading parts are shared (prefix)
            min_parts = min(len(parts) for parts in split_labels)
            shared_prefix_count = 0
            for i in range(min_parts - 1):
                first_part = split_labels[0][i]
                if all(parts[i] == first_part for parts in split_labels):
                    shared_prefix_count += 1
                else:
                    break

            # Find how many trailing parts are shared (suffix)
            shared_suffix_count = 0
            for i in range(1, min_parts):
                last_part = split_labels[0][-i]
                if all(parts[-i] == last_part for parts in split_labels):
                    shared_suffix_count += 1
                else:
                    break

            # Use whichever is longer (prefix or suffix), prefer suffix for IRFCL
            if shared_suffix_count > 0 and shared_suffix_count >= shared_prefix_count:
                suffix_parts = split_labels[0][-shared_suffix_count:]
                # Reverse so outermost (last part) is created first as parent
                suffix_parts_reversed = list(reversed(suffix_parts))
                first_child_order = min(c.get("order", 0) for c in path_children)
                first_child_depth = path_children[0].get("depth", 0)
                # Create nested synthetic groups
                current_parent_id = parent_id
                current_depth = first_child_depth
                innermost_synthetic_id = None

                for i, suffix_part in enumerate(suffix_parts_reversed):
                    synthetic_id = f"_SYNTH_{current_parent_id}_{re.sub(r'[^a-zA-Z0-9]', '_', suffix_part[:30])}_{i}"
                    synthetic_group = {
                        "id": synthetic_id,
                        "indicator_code": None,
                        "label": suffix_part,
                        "description": "",
                        "order": first_child_order - 0.5 + (i * 0.01),
                        "level": current_depth,
                        "depth": current_depth,
                        "parent_id": current_parent_id,
                        "is_group": True,
                        "code_urn": None,
                        "dimension_id": None,
                        "series_id": None,
                    }
                    synthetic_groups.append(synthetic_group)
                    # Next group will be child of this one
                    current_parent_id = synthetic_id
                    current_depth += 1
                    innermost_synthetic_id = synthetic_id

                # re-parent to innermost synthetic group and remove suffix
                for child in path_children:
                    child_parts = child["label"].split(", ")
                    remaining_parts = child_parts[:-shared_suffix_count]
                    if remaining_parts:
                        child["label"] = ", ".join(remaining_parts)
                    child["parent_id"] = innermost_synthetic_id
                    child["depth"] = current_depth
                    child["depth"] = first_child_depth + 1

            elif shared_prefix_count > 0:
                # Create group from shared prefix
                shared_prefix = ", ".join(split_labels[0][:shared_prefix_count])
                synthetic_id = f"_SYNTH_{parent_id}_{re.sub(r'[^a-zA-Z0-9]', '_', shared_prefix[:30])}"
                first_child_order = min(c.get("order", 0) for c in path_children)
                first_child_depth = path_children[0].get("depth", 0)
                synthetic_group = {
                    "id": synthetic_id,
                    "indicator_code": None,
                    "label": shared_prefix,
                    "description": "",
                    "order": first_child_order - 0.5,
                    "level": first_child_depth,
                    "depth": first_child_depth,
                    "parent_id": parent_id,
                    "is_group": True,
                    "code_urn": None,
                    "dimension_id": None,
                    "series_id": None,
                }
                synthetic_groups.append(synthetic_group)

                # re-parent and remove prefix
                for child in path_children:
                    child_parts = child["label"].split(", ")
                    remaining_parts = child_parts[shared_prefix_count:]
                    if remaining_parts:
                        child["label"] = ", ".join(remaining_parts)
                    child["parent_id"] = synthetic_id
                    child["depth"] = first_child_depth + 1

        # Merge synthetic groups into indicators list
        if synthetic_groups:
            all_indicators = indicators + synthetic_groups
            all_indicators.sort(key=lambda x: x.get("order", 0))
            for i, ind in enumerate(all_indicators):
                ind["order"] = i + 1
            # After creating one level of groups, the children may still
            # have shared prefixes/suffixes that need another level of grouping
            return self._create_synthetic_groups_for_shared_prefixes(all_indicators)

        return indicators