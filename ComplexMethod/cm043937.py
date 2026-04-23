def get_dataflow_table_structure(
        self, dataflow_id: str, table_id: str | None = None
    ) -> dict:
        """
        Get the presentation table structure for a dataflow.

        Handles both hierarchy-based (hierarchy.json) and embedded presentations.

        Parameters
        ----------
        dataflow_id : str
            The dataflow ID
        table_id : str | None
            The specific hierarchy/table ID. If None, uses the first available.

        Returns
        -------
        dict
            Structure with hierarchy metadata and nested indicators.
        """
        available_hierarchies = self.get_dataflow_hierarchies(dataflow_id)

        if not available_hierarchies:
            raise ValueError(
                f"No presentation hierarchies found for dataflow '{dataflow_id}'"
            )

        # Track if this is a split table (one top-level code from a multi-code hierarchy)
        top_level_code_filter: str | None = None
        base_hierarchy_id: str | None = None

        if table_id:
            # Find the specific table
            selected_table = None
            for h in available_hierarchies:
                if h["id"] == table_id:
                    selected_table = h
                    break
            if not selected_table:
                raise ValueError(
                    f"Hierarchy '{table_id}' not found. "
                    f"Available: {[h['id'] for h in available_hierarchies]}"
                )
            # Check if this is a split table (format: "base_id:top_level_code_id")
            if ":" in table_id:
                base_hierarchy_id, top_level_code_filter = table_id.split(":", 1)
            else:
                base_hierarchy_id = table_id
        else:
            selected_table = available_hierarchies[0]
            table_id = selected_table.get("id", "")
            if table_id and ":" in table_id:
                base_hierarchy_id, top_level_code_filter = table_id.split(":", 1)
            else:
                base_hierarchy_id = table_id

        # Handle hierarchy-based presentations
        # Use base_hierarchy_id to look up the actual hierarchy object
        hierarchy = self.hierarchies.get(base_hierarchy_id or table_id)
        if not hierarchy:
            raise ValueError(
                f"Hierarchy '{base_hierarchy_id or table_id}' not found in cache"
            )

        if not table_id:
            raise ValueError("table_id cannot be None")

        codelist_id = self._hierarchy_to_codelist_map.get(base_hierarchy_id or table_id)

        dataflow_obj = self.dataflows.get(dataflow_id, {})
        agency_id = dataflow_obj.get("agencyID", "IMF")
        agency_clean = agency_id.replace(".", "_")

        structure_ref = dataflow_obj.get("structureRef", {})
        dsd_id = structure_ref.get("id")
        dsd_obj = self.datastructures.get(dsd_id, {}) if dsd_id else {}
        dimensions = dsd_obj.get("dimensions", []) if isinstance(dsd_obj, dict) else []

        indicator_dimension_order: dict[str, int] = {}
        indicator_id_candidates = [
            "INDICATOR",
            "PRODUCTION_INDEX",
            "COICOP_1999",
            "ACTIVITY",
            "PRODUCT",
            "SERIES",
            "ITEM",
            "BOP_ACCOUNTING_ENTRY",
            "ACCOUNTING_ENTRY",
        ]

        for idx, dim in enumerate(dimensions):
            dim_id = dim.get("id", "")
            if not dim_id:
                continue
            is_indicator_candidate = dim_id in indicator_id_candidates or any(
                keyword in dim_id
                for keyword in ["INDICATOR", "ACCOUNTING_ENTRY", "ENTRY"]
            )
            if is_indicator_candidate:
                indicator_dimension_order[dim_id] = idx

        codelist_dimension_cache: dict[str, str | None] = {}
        # Cache for per-codelist label and description lookups
        # Hierarchies can mix codes from multiple codelists (e.g., CL_BOP_INDICATOR + CL_BOP_ACCOUNTING_ENTRY)
        codelist_labels_cache: dict[str, dict] = {}
        codelist_desc_cache: dict[str, dict] = {}

        def process_hierarchical_codes(
            codes: list,
            parent_id: str | None = None,
            depth: int = 0,
            parent_codes: list | None = None,
            parent_dimension_codes: dict[str, str] | None = None,
            order_counter: list | None = None,
            parent_full_label: str | None = None,
            ancestor_labels: list | None = None,
        ) -> list[dict]:
            """Recursively process hierarchical codes into flat indicator list."""
            # pylint: disable=import-outside-toplevel
            import re

            indicators = []

            if parent_codes is None:
                parent_codes = []
            if parent_dimension_codes is None:
                parent_dimension_codes = {}
            if order_counter is None:
                order_counter = [0]
            if ancestor_labels is None:
                ancestor_labels = []

            for code_entry in codes:
                code_id = code_entry.get("id")
                code_urn = code_entry.get("code", "")
                level = code_entry.get("level", "0")
                indicator_code = self._parse_indicator_code_from_urn(code_urn)
                codelist_id_for_code = self._parse_codelist_id_from_urn(code_urn)
                dimension_id = None

                if codelist_id_for_code:
                    if codelist_id_for_code not in codelist_dimension_cache:
                        codelist_dimension_cache[codelist_id_for_code] = (
                            self._get_dimension_for_codelist(
                                dataflow_id, codelist_id_for_code
                            )
                        )
                    dimension_id = codelist_dimension_cache[codelist_id_for_code]
                    # Cache labels and descriptions for this codelist
                    # Check if not in cache OR if cached value is empty (failed previous fetch)
                    cached_is_empty = not codelist_labels_cache.get(
                        codelist_id_for_code
                    )
                    if (
                        codelist_id_for_code not in codelist_labels_cache
                        or cached_is_empty
                    ):
                        # Try to get from main cache first
                        cached_labels = self._codelist_cache.get(
                            codelist_id_for_code, {}
                        )
                        cached_descs = self._codelist_descriptions.get(
                            codelist_id_for_code, {}
                        )
                        # If not found, try to fetch from API using URN agency
                        if not cached_labels and code_urn:
                            urn_agency = self._parse_agency_from_urn(code_urn)
                            if urn_agency:
                                self._fetch_single_codelist(
                                    urn_agency, codelist_id_for_code
                                )
                                cached_labels = self._codelist_cache.get(
                                    codelist_id_for_code, {}
                                )
                                cached_descs = self._codelist_descriptions.get(
                                    codelist_id_for_code, {}
                                )
                        codelist_labels_cache[codelist_id_for_code] = cached_labels
                        codelist_desc_cache[codelist_id_for_code] = cached_descs

                # Look up label from the code's actual codelist, not just the owning codelist
                code_labels = (
                    codelist_labels_cache.get(codelist_id_for_code, {})
                    if codelist_id_for_code
                    else {}
                )
                code_descs = (
                    codelist_desc_cache.get(codelist_id_for_code, {})
                    if codelist_id_for_code
                    else {}
                )
                full_label = (
                    code_labels.get(indicator_code, code_id)
                    if indicator_code
                    else code_id
                )
                # Detect path-based labels in INDICATOR_PUB codelists
                # These codelists store labels as comma-separated hierarchical paths
                # e.g., "Section A, Category B, Item C" -> extract relative portion
                # The hierarchy provides context, so we only need what's NEW at this node
                label = full_label
                # Check if this codelist uses path-style labels:
                # 1. Named pattern: "_INDICATOR_PUB" in codelist name
                # 2. Explicit codelist: CL_DIP_INDICATOR uses path-style labels
                is_path_style_codelist = codelist_id_for_code and (
                    "_INDICATOR_PUB" in codelist_id_for_code
                    or codelist_id_for_code == "CL_DIP_INDICATOR"
                )
                if is_path_style_codelist:
                    # Special case for CL_DIP_INDICATOR: the first part of every label
                    # is "Inward Direct investment" or "Outward Direct investment" which
                    # is redundant with the parent categories "Inward Indicators"/"Outward Indicators"
                    # Just skip the first part for DIP labels
                    if (
                        codelist_id_for_code == "CL_DIP_INDICATOR"
                        and ", " in full_label
                    ):
                        parts = full_label.split(", ")
                        if len(parts) > 1 and (
                            parts[0].startswith("Inward")
                            or parts[0].startswith("Outward")
                        ):
                            label = ", ".join(parts[1:])
                    # For other path-style codelists, try exact prefix match with parent's full label
                    elif parent_full_label and full_label.startswith(parent_full_label):
                        # Remove parent's label prefix and separator
                        relative_label = full_label[len(parent_full_label) :].lstrip(
                            ", :"
                        )
                        if relative_label:
                            label = relative_label
                        elif ", " in full_label or ": " in full_label:
                            # Child has same label as parent (e.g., USD vs FTO gold variants)
                            parts = re.split(r", |: ", full_label)
                            label = parts[-1] if parts else full_label
                    elif ancestor_labels and (", " in full_label or ": " in full_label):
                        # This handles cases where hierarchy mixes codelists
                        def normalize_part(s: str) -> str:
                            """Normalize for comparison: lowercase, remove punctuation."""
                            return re.sub(r"[^a-z0-9]", "", s.lower())

                        # Split label by both ", " and ":" separators
                        def split_label(lbl: str) -> list:
                            """Split by comma-space and colon."""
                            # First split by ", "
                            parts = lbl.split(", ")
                            # Then split each part by ":"
                            result = []
                            for p in parts:
                                if ":" in p:
                                    subparts = p.split(":")
                                    result.extend(
                                        [sp.strip() for sp in subparts if sp.strip()]
                                    )
                                else:
                                    result.append(p)
                            return result

                        # Collect all parts from all ancestor labels
                        all_ancestor_parts = []
                        for anc_label in ancestor_labels:
                            all_ancestor_parts.extend(split_label(anc_label))

                        child_parts = split_label(full_label)

                        # Build set of normalized ancestor parts
                        ancestor_normalized = {
                            normalize_part(p) for p in all_ancestor_parts
                        }

                        # Find parts in child that are genuinely new
                        new_parts = []
                        for part in child_parts:
                            part_norm = normalize_part(part)
                            # Allow for "Total X" in ancestor matching "X" in child
                            is_in_ancestor = part_norm in ancestor_normalized
                            if not is_in_ancestor:
                                for pn in ancestor_normalized:
                                    # Check "totalX" matching "X"
                                    if pn.startswith("total") and pn[5:] == part_norm:
                                        is_in_ancestor = True
                                        break
                                    # Check if ancestor part is contained in child part
                                    # e.g., "outflows" in "outflowsreservestemplate"
                                    if len(pn) >= 6 and pn in part_norm:
                                        is_in_ancestor = True
                                        break
                                    # Check if strings are very similar (>80% overlap)
                                    # This handles encoding differences like "visvis" vs "vissvis"
                                    # and inconsistent comma placement in IMF data
                                    if len(part_norm) >= 15 and len(pn) >= 15:
                                        # Check if one contains most of the other
                                        shorter = min(part_norm, pn, key=len)
                                        longer = max(part_norm, pn, key=len)
                                        # If 80%+ of shorter is in longer, consider match
                                        if shorter in longer or (
                                            len(shorter) > 30
                                            and any(
                                                shorter[i : i + 30] in longer
                                                for i in range(len(shorter) - 30)
                                            )
                                        ):
                                            is_in_ancestor = True
                                            break
                            if not is_in_ancestor:
                                new_parts.append(part)

                        if new_parts:
                            # For IRFCL path labels, keep all parts
                            if (
                                codelist_id_for_code
                                and "IRFCL" in codelist_id_for_code
                                and len(new_parts) >= 3
                            ):
                                # Keep the full label - synthetic groups will organize it
                                label = ", ".join(new_parts)
                            else:
                                label = (
                                    ", ".join(new_parts)
                                    if new_parts
                                    else child_parts[-1] if child_parts else full_label
                                )
                        else:
                            label = child_parts[-1] if child_parts else full_label
                    elif ", " in full_label:
                        # No ancestors - this is a top-level node
                        # Take just the LAST part as the actual indicator label
                        parts = full_label.split(", ")
                        label = parts[-1] if parts else full_label
                elif (
                    parent_full_label
                    and ", " in full_label
                    and full_label.startswith(parent_full_label)
                ):
                    # For other codelists, check if parent's label is a prefix
                    label = full_label.rsplit(", ", 1)[-1]
                description = (
                    code_descs.get(indicator_code, "") if indicator_code else ""
                )

                children = code_entry.get("hierarchicalCodes", [])
                is_group = len(children) > 0

                current_dimension_codes = parent_dimension_codes.copy()
                if dimension_id and indicator_code:
                    current_dimension_codes[dimension_id] = indicator_code

                # Clean parent_id: if it contains codelist prefix, extract just the code
                clean_parent_id = parent_id
                if parent_id and "___" in parent_id:
                    clean_parent_id = parent_id.split("___")[-1]

                # Assign sequential order to ALL nodes (groups and leaf nodes)
                order_counter[0] += 1
                current_order = order_counter[0]

                # For BOP dataflows, use depth (actual nesting) instead of IMF's
                # inconsistent level attribute
                use_depth_for_level = dataflow_id in ("BOP", "BOP_AGG", "IIP", "IIPCC")
                node_level = (
                    depth if use_depth_for_level else (int(level) if level else depth)
                )

                indicator_info = {
                    "id": code_id,
                    "indicator_code": indicator_code,
                    "label": label,
                    "description": description,
                    "order": current_order,
                    "level": node_level,
                    "depth": depth,
                    "parent_id": clean_parent_id,
                    "is_group": is_group,
                    "code_urn": code_urn,
                    "dimension_id": dimension_id,
                }

                # Only build series_id if indicator_code belongs to a queryable dimension
                if indicator_code and dimension_id:
                    # Filter to only dimensions that have a known position
                    ordered_dims = sorted(
                        [
                            (dim_id_iter, indicator_dimension_order[dim_id_iter])
                            for dim_id_iter in current_dimension_codes
                            if dim_id_iter in indicator_dimension_order
                            and current_dimension_codes.get(dim_id_iter)
                        ],
                        key=lambda item: item[1],
                    )
                    ordered_codes = [
                        current_dimension_codes[dim_id_iter]
                        for dim_id_iter, _ in ordered_dims
                    ]
                    unordered_dims = [
                        dim_id_iter
                        for dim_id_iter in current_dimension_codes
                        if dim_id_iter not in indicator_dimension_order
                        and current_dimension_codes.get(dim_id_iter)
                    ]
                    ordered_codes.extend(
                        [
                            current_dimension_codes[dim_id_iter]
                            for dim_id_iter in sorted(unordered_dims)
                        ]
                    )

                    if ordered_codes:
                        combined_codes = "_".join(ordered_codes)
                        indicator_info["series_id"] = (
                            f"{agency_clean}_{dataflow_id}_{combined_codes}"
                        )
                    else:
                        # Fallback to parent code ordering when dimension mapping fails
                        fallback_codes = parent_codes + [indicator_code]
                        indicator_info["series_id"] = (
                            f"{agency_clean}_{dataflow_id}_{'_'.join(fallback_codes)}"
                        )

                indicators.append(indicator_info)

                if children:
                    child_parent_codes = parent_codes + (
                        [indicator_code] if indicator_code else []
                    )
                    # Accumulate ancestor labels for path-based label extraction
                    child_ancestor_labels = ancestor_labels + [full_label]
                    child_indicators = process_hierarchical_codes(
                        children,
                        parent_id=code_id,
                        depth=depth + 1,
                        parent_codes=child_parent_codes,
                        parent_dimension_codes=current_dimension_codes.copy(),
                        order_counter=order_counter,
                        parent_full_label=full_label,
                        ancestor_labels=child_ancestor_labels,
                    )
                    indicators.extend(child_indicators)

            return indicators

        hierarchical_codes = hierarchy.get("hierarchicalCodes", [])

        # If a top-level code filter is set, only include that specific top-level code
        if top_level_code_filter:
            filtered_codes = [
                c for c in hierarchical_codes if c.get("id") == top_level_code_filter
            ]
            if filtered_codes:
                hierarchical_codes = filtered_codes

        indicators = process_hierarchical_codes(hierarchical_codes)

        # Post-processing: Fix IRFCL hierarchy issues
        if dataflow_id == "IRFCL":
            indicators = self._fix_irfcl_hierarchy(indicators)

        # Get table name from selected_table if available (for split tables)
        table_name = (
            selected_table.get("name", hierarchy.get("name"))
            if selected_table
            else hierarchy.get("name")
        )

        return {
            "hierarchy_id": table_id,  # Use full table_id including split suffix
            "hierarchy_name": table_name,
            "hierarchy_description": hierarchy.get("description", ""),
            "dataflow_id": dataflow_id,
            "codelist_id": codelist_id,
            "agency_id": hierarchy.get("agencyID"),
            "version": hierarchy.get("version"),
            "indicators": indicators,
            "total_indicators": len([i for i in indicators if not i["is_group"]]),
            "total_groups": len([i for i in indicators if i["is_group"]]),
            "type": "hierarchy",
        }