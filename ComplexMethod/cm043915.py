def pivot_table_mode(
    df: "pd.DataFrame",
    dates: list[Any],
    countries: list[str],
    metadata: dict[str, Any],
) -> "pd.DataFrame":
    """Get a hierarchical pivot for table mode.

    Handles:
    - Parent/child hierarchy detection
    - Title simplification based on displayed ancestors
    - Proper indentation with visual hierarchy markers
    - Uniform vs per-row unit display
    - Hierarchy name headers

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing IMF indicator data.
    dates : list[Any]
        List of dates to use as columns.
    countries : list[str]
        List of countries.
    metadata : dict[str, Any]
        Metadata dictionary containing table information.

    Returns
    -------
    pd.DataFrame
        Pivoted DataFrame with hierarchical structure.
    """
    # pylint: disable=import-outside-toplevel
    from collections import defaultdict

    import pandas as pd

    # Build the hierarchy context
    order_title_level = build_order_title_level(df)
    hierarchy_ctx = HierarchyContext(order_title_level)

    # Detect ISORA-style tables (topic hierarchy, dash-delimited labels)
    table_name = metadata.get("table", {}).get("hierarchy_name", "")
    dataflow_id = metadata.get("table", {}).get("dataflow_id", "")
    is_isora = "ISORA" in dataflow_id or "INDICATORS BY TOPIC" in table_name.upper()

    # Build helper maps for unit/scale inheritance
    node_id_to_order: dict[str, int | float] = {}
    for node_row in df.itertuples(index=False):
        node_id = getattr(node_row, "hierarchy_node_id", None)
        order_val = getattr(node_row, "order", None)
        if node_id and order_val is not None:
            node_id_to_order[str(node_id)] = order_val

    order_to_parent: dict[int | float, int | float] = {}
    for order_val in df["order"].dropna().unique():
        order_df = df[df["order"] == order_val]
        first_row = order_df.iloc[0]
        parent_id = first_row.get("parent_id")
        parent_order: int | float | None = None
        if parent_id:
            parent_id_str = str(parent_id)
            parent_order = node_id_to_order.get(parent_id_str)
            if parent_order is None:
                suffix_pattern = f"___{parent_id_str}"
                for node_id, node_order in node_id_to_order.items():
                    if node_id.endswith(suffix_pattern):
                        parent_order = node_order
                        break
        if parent_order is not None:
            order_to_parent[order_val] = parent_order

    # Capture unit/scale per order (from explicit columns or suffix) and inherit down
    unit_scale_by_order: dict[int | float, tuple[str | None, str | None]] = {}

    for order_val in df["order"].dropna().unique():
        order_df = df[df["order"] == order_val]
        unit_val: str | None = None
        scale_val: str | None = None

        for _, row in order_df.iterrows():
            if unit_val is None:
                candidate_unit = row.get("unit")
                if candidate_unit and str(candidate_unit) != "nan":
                    unit_val = str(candidate_unit)
            if scale_val is None:
                candidate_scale = row.get("scale")
                if candidate_scale and str(candidate_scale) != "nan":
                    scale_val = str(candidate_scale)

            if unit_val is None or scale_val is None:
                parsed_unit, parsed_scale = extract_unit_scale_from_title(
                    str(row.get("title") or "")
                )
                if unit_val is None and parsed_unit:
                    unit_val = parsed_unit
                if scale_val is None and parsed_scale:
                    scale_val = parsed_scale

            if unit_val is not None and scale_val is not None:
                break

        unit_scale_by_order[order_val] = (unit_val, scale_val)
    for order_val in list(unit_scale_by_order.keys()):
        unit_val, scale_val = unit_scale_by_order[order_val]
        if unit_val is not None and scale_val is not None:
            continue

        visited: set[int | float] = set()
        parent_order = order_to_parent.get(order_val)
        while parent_order is not None and parent_order not in visited:
            visited.add(parent_order)
            p_unit, p_scale = unit_scale_by_order.get(parent_order, (None, None))
            if unit_val is None and p_unit is not None:
                unit_val = p_unit
            if scale_val is None and p_scale is not None:
                scale_val = p_scale
            if unit_val is not None and scale_val is not None:
                break
            parent_order = order_to_parent.get(parent_order)

        unit_scale_by_order[order_val] = (unit_val, scale_val)

    # First pass: collect RAW data rows and track which orders have actual data
    # Title simplification is deferred until we know which ancestors will be displayed
    orders_with_data: set[int | float] = set()
    raw_data_rows: list[dict[str, Any]] = []

    # Include ALL orders that might have data - don't exclude category headers
    # because they can also have data values (aggregates)
    data_orders = df["order"].dropna().unique()

    for order in sorted(data_orders):
        order_df = df[df["order"] == order]

        # Data rows - one per country, per series/dimension combination
        for country in countries:
            country_df = order_df[order_df["country"] == country]
            if country_df.empty:
                continue

            # Determine grouping columns - use series_id if available, otherwise
            # group by dimension code columns to separate different series
            # ALWAYS include dimension code columns to separate by counterpart_country, etc.
            # Exclude dv_type_code - it's just "Reported official data" for everything
            dim_code_cols = [
                c
                for c in country_df.columns
                if c.endswith("_code")
                and c not in ("country_code", "frequency_code", "dv_type_code")
                and country_df[c].notna().any()
            ]
            if "series_id" in country_df.columns:
                # Include series_id AND dimension codes
                group_cols = ["series_id"] + [
                    c for c in dim_code_cols if c != "series_id"
                ]
            else:
                group_cols = dim_code_cols if dim_code_cols else ["symbol"]

            # Ensure all group columns exist and handle NaN
            valid_group_cols = [c for c in group_cols if c in country_df.columns]
            if not valid_group_cols:
                valid_group_cols = ["symbol"] if "symbol" in country_df.columns else []

            if valid_group_cols:
                for _, series_df in country_df.groupby(valid_group_cols, dropna=False):
                    if series_df.empty:
                        continue
                    first_in_series = series_df.iloc[0]

                    # Check if this series has ANY data for the selected dates
                    has_data = False
                    row_values: dict[str, Any] = {}
                    for d in dates:
                        # Handle date comparison - d may be string or datetime.date
                        # series_df["date"] may also be either type
                        d_str = str(d)
                        date_matches = series_df["date"].astype(str) == d_str
                        val = series_df[date_matches]["value"].values
                        if len(val) > 0 and pd.notna(val[0]):
                            row_values[str(d)] = val[0]
                            has_data = True
                        else:
                            row_values[str(d)] = None

                    if has_data:
                        orders_with_data.add(order)

                        # Store RAW title - simplification deferred
                        title = first_in_series.get("title", "")
                        if not title:
                            ind_code = first_in_series.get("indicator_code", "")
                            if ind_code:
                                title = ind_code.replace("_", " ").capitalize()

                        row_unit = first_in_series.get("unit") or ""
                        row_scale = first_in_series.get("scale") or ""

                        # Fallback to order-level (inherited) unit/scale when missing
                        inherited_unit, inherited_scale = unit_scale_by_order.get(
                            order, (None, None)
                        )

                        if not row_unit and inherited_unit:
                            row_unit = inherited_unit
                        if not row_scale and inherited_scale:
                            row_scale = inherited_scale

                        # As a last resort, parse the title suffix for unit/scale
                        if not row_unit or not row_scale:
                            parsed_unit, parsed_scale = extract_unit_scale_from_title(
                                title
                            )
                            if not row_unit and parsed_unit:
                                row_unit = parsed_unit
                            if not row_scale and parsed_scale:
                                row_scale = parsed_scale

                        # Collect dimension values for grouping headers
                        # Look for *_code fields that indicate dimension breakdowns
                        # Column names in the data are lowercase (sector_code, gfs_grp_code, etc.)
                        dimension_values: dict[str, tuple[str, str]] = {}
                        # Dimensions that should create grouping headers
                        # Keys are uppercase (for display), values are lowercase (for column lookup)
                        grouping_dims = {
                            "SECTOR": "sector",
                            "TYPE_OF_TRANSFORMATION": "type_of_transformation",
                            "COUNTERPART_COUNTRY": "counterpart_country",
                            "CURRENCY": "currency",
                            "INDEX_TYPE": "index_type",
                            "BOP_ACCOUNTING_ENTRY": "bop_accounting_entry",
                            "ACCOUNTING_ENTRY": "accounting_entry",
                            "ACCOUNT": "account",
                            "PRICE_TYPE": "price_type",
                            "S_ADJUSTMENT": "s_adjustment",
                        }
                        for dim_id, col_name in grouping_dims.items():
                            code_key = f"{col_name}_code"
                            code_val = first_in_series.get(code_key)
                            label_val = first_in_series.get(col_name)
                            if code_val and label_val:
                                dimension_values[dim_id] = (
                                    str(code_val),
                                    str(label_val),
                                )

                        raw_data_rows.append(
                            {
                                "order": order,
                                "level": first_in_series["level"] or 0,
                                "raw_title": title,  # Store raw title
                                "country": country,
                                "values": row_values,
                                "unit": row_unit,
                                "scale": row_scale,
                                "dimension_values": dimension_values,
                            }
                        )

    # Find all parent orders that lead to data rows
    parent_orders: set[int | float] = set()
    true_header_parents: set[int | float] = set()

    for order in orders_with_data:
        order_df = df[df["order"] == order]
        if len(order_df) == 0:
            continue
        parent_id = order_df.iloc[0].get("parent_id")
        # Trace up the hierarchy to find all parent headers
        while parent_id:
            parent_df = df[df["hierarchy_node_id"] == parent_id]
            # hierarchy_node_id might be "CL_X___CODE" but parent_id is just "CODE"
            if len(parent_df) == 0:
                suffix_pattern = f"___{parent_id}"
                parent_df = df[
                    df["hierarchy_node_id"].fillna("").str.endswith(suffix_pattern)
                ]
            if len(parent_df) == 0:
                break
            parent_order = parent_df.iloc[0]["order"]
            parent_is_header = parent_df.iloc[0].get("is_category_header", False)
            if parent_order is not None:
                parent_orders.add(parent_order)
                # Track true headers separately for title stripping
                if parent_is_header:
                    true_header_parents.add(parent_order)
            parent_id = parent_df.iloc[0].get("parent_id")

    # Build per-country orders_with_data
    country_orders_with_data: dict[str, set[int | float]] = {}
    for raw_row in raw_data_rows:
        country = raw_row["country"]
        order = raw_row["order"]
        if country not in country_orders_with_data:
            country_orders_with_data[country] = set()
        country_orders_with_data[country].add(order)

    # Build per-country parent_orders (ancestors of data rows for each country)
    country_parent_orders: dict[str, set[int | float]] = {}
    for country, country_data_orders in country_orders_with_data.items():
        country_parents: set[int | float] = set()
        for order in country_data_orders:
            order_df = df[df["order"] == order]
            if len(order_df) == 0:
                continue
            parent_id = order_df.iloc[0].get("parent_id")
            while parent_id:
                parent_df = df[df["hierarchy_node_id"] == parent_id]
                if len(parent_df) == 0:
                    suffix_pattern = f"___{parent_id}"
                    parent_df = df[
                        df["hierarchy_node_id"].fillna("").str.endswith(suffix_pattern)
                    ]
                if len(parent_df) == 0:
                    break
                parent_order = parent_df.iloc[0]["order"]
                if parent_order is not None:
                    country_parents.add(parent_order)
                parent_id = parent_df.iloc[0].get("parent_id")
        country_parent_orders[country] = country_parents

    # Compute the union of all per-country parent orders
    # This ensures we only show headers that lead to data for at least one country in the result
    effective_parent_orders: set[int | float] = set()
    for country_parents in country_parent_orders.values():
        effective_parent_orders.update(country_parents)

    data_rows: list[dict[str, Any]] = []

    for raw_row in raw_data_rows:
        order = raw_row["order"]
        title = raw_row["raw_title"]
        country = raw_row["country"]
        country_data_orders = country_orders_with_data.get(country, set())
        displayed_orders = true_header_parents | country_data_orders
        title = hierarchy_ctx.simplify_title(order, title, displayed_orders)

        data_rows.append(
            {
                "order": order,
                "level": raw_row["level"],
                "title": title,
                "country": raw_row["country"],
                "values": raw_row["values"],
                "unit": raw_row["unit"],
                "scale": raw_row["scale"],
                "dimension_values": raw_row.get("dimension_values", {}),
            }
        )

    # Detect which dimensions have multiple values (need grouping headers)
    dim_value_sets: dict[str, set[str]] = {}
    for dr in data_rows:
        for dim_id, (code, label) in dr.get("dimension_values", {}).items():
            if dim_id not in dim_value_sets:
                dim_value_sets[dim_id] = set()
            dim_value_sets[dim_id].add(code)

    # Dimensions with multiple values need synthetic grouping headers
    multi_value_dims = [
        dim_id for dim_id, codes in dim_value_sets.items() if len(codes) > 1
    ]

    # If we have multi-value dimensions, add grouping info to data rows
    if multi_value_dims:
        # Sort multi_value_dims in a sensible order (SECTOR first, then others)
        dim_priority = {"SECTOR": 0, "GFS_GRP": 1, "TYPE_OF_TRANSFORMATION": 2}
        multi_value_dims.sort(key=lambda d: dim_priority.get(d, 99))

        for dr in data_rows:
            dim_vals = dr.get("dimension_values", {})
            # Build grouping key from multi-value dimensions
            grouping_parts = []
            for dim_id in multi_value_dims:
                if dim_id in dim_vals:
                    code, label = dim_vals[dim_id]
                    grouping_parts.append((dim_id, code, label))
            dr["_grouping_dims"] = grouping_parts

        # Sort data rows by (grouping dimensions, order) for proper grouping
        # This groups all items with the same dimension values together,
        # then sorts by hierarchical order within each group
        def row_sort_key(row: dict) -> tuple:
            grouping = tuple(
                (dim_id, code) for dim_id, code, label in row.get("_grouping_dims", [])
            )
            order_val = row.get("order", 0)
            return grouping + (order_val,)

        data_rows.sort(key=row_sort_key)

    # Note: ISORA tables use dash-delimited titles but we do NOT create synthetic
    # headers from them as it causes false groupings (e.g., "On" from "On-time").
    # Instead, we rely on the existing hierarchy metadata (topic parent nodes).

    # Check if all data rows have the same unit and scale
    all_units = {dr.get("unit") for dr in data_rows if dr.get("unit")}
    all_scales = {dr.get("scale") for dr in data_rows if dr.get("scale")}
    uniform_unit = all_units.pop() if len(all_units) == 1 else None
    uniform_scale = all_scales.pop() if len(all_scales) == 1 else None
    # If there are multiple units, we need per-row display even if scale is uniform
    has_uniform_unit_scale = uniform_unit is not None
    uniform_suffix = ""

    if has_uniform_unit_scale:
        parts = []
        if uniform_unit:
            parts.append(uniform_unit)
        if uniform_scale and uniform_scale != "Units":
            parts.append(uniform_scale)
        if parts:
            uniform_suffix = f" ({', '.join(parts)})"

    # Check if we need to add a hierarchy name header
    hierarchy_name = metadata.get("table", {}).get("hierarchy_name")
    first_level_0_is_data = False
    first_level_0_title = None

    for order in sorted(df["order"].unique()):
        order_df = df[df["order"] == order]
        first = order_df.iloc[0]
        level = first["level"] or 0

        if level == 0:
            is_header = first["is_category_header"]
            first_level_0_title = first["title"] or ""

            if not is_header:
                first_level_0_is_data = True
            break

    # Add it if: (1) first level-0 is data, OR (2) hierarchy name differs from first level-0 title
    should_add_table_header = False

    if hierarchy_name:
        if first_level_0_is_data:
            should_add_table_header = True
        elif first_level_0_title:
            hierarchy_name_clean = hierarchy_name.upper().replace("_", " ")
            first_title_clean = first_level_0_title.upper().split(" (")[0]
            if (
                hierarchy_name_clean not in first_title_clean
                and first_title_clean not in hierarchy_name_clean
            ):
                should_add_table_header = True

    # Second pass: build final rows with headers that have data children
    rows: list[dict[str, Any]] = []

    if should_add_table_header and hierarchy_name:
        header_title = hierarchy_name.upper()
        if uniform_suffix:
            header_title += uniform_suffix
        row = {
            "title": f"▸ {header_title}",
            "country": "",
        }
        for d in dates:
            row[str(d)] = ""
        rows.append(row)

    all_orders = list(df["order"].unique())
    sorted_orders = sorted(all_orders, key=lambda o: float(o))  # pylint: disable=W0108

    # Universal dimension grouping, when multi_value_dims exists
    dim_group_map: dict[tuple, list[dict]] = defaultdict(list)
    if multi_value_dims:
        for dr in data_rows:
            grouping_key = tuple(dr.get("_grouping_dims", []))
            dim_group_map[grouping_key].append(dr)
    else:
        dim_group_map[()] = data_rows

    def format_dim_labels(grouping_key: tuple) -> str:
        """Format all dimension labels from a grouping key into a display string.

        Excludes TYPE_OF_TRANSFORMATION when its value is a unit-like label
        (e.g., "Domestic currency") since that's already shown in the parent
        row's unit suffix. Keeps meaningful transformation types like "Index",
        "Percent change", etc.
        """
        if not grouping_key:
            return ""

        # Unit-like transformation values to exclude (already shown in parent suffix)
        unit_like_transformations = {
            "Domestic currency",
            "National currency",
            "US dollar",
            "US Dollar",
            "SDR",
            "Euro",
        }

        labels = []
        filtered_labels = []
        for dim_id, _, label in grouping_key:
            labels.append(label)
            if (
                dim_id == "TYPE_OF_TRANSFORMATION"
                and label in unit_like_transformations
            ):
                continue
            filtered_labels.append(label)

        # If filtering removed everything, fall back to the unfiltered labels so we
        # never render a blank title row for unit-only dimensions.
        effective_labels = filtered_labels if filtered_labels else labels

        return " - ".join(effective_labels) if effective_labels else ""

    # Build a map of order -> list of (grouping_key, data_rows_for_order)
    # Preserve original data order by iterating data_rows directly
    order_to_dim_data: dict[int | float, list[tuple[tuple, list[dict]]]] = defaultdict(
        list
    )
    seen_order_keys: dict[int | float, set[tuple]] = defaultdict(set)

    for dr in data_rows:
        order = dr["order"]
        grouping_key = tuple(dr.get("_grouping_dims", []))

        if grouping_key in seen_order_keys[order]:
            # Find existing entry and append
            for entry in order_to_dim_data[order]:
                if entry[0] == grouping_key:
                    entry[1].append(dr)
                    break
        else:
            # New grouping key for this order - add in data order
            order_to_dim_data[order].append((grouping_key, [dr]))
            seen_order_keys[order].add(grouping_key)

    # Compute parent orders globally (across all dimension groups)
    all_orders_with_data = {dr["order"] for dr in data_rows}
    global_parent_orders: set[int | float] = set()
    for order in all_orders_with_data:
        order_df = df[df["order"] == order]
        if len(order_df) == 0:
            continue
        parent_id = order_df.iloc[0].get("parent_id")
        while parent_id:
            parent_df = df[df["hierarchy_node_id"] == parent_id]
            if len(parent_df) == 0:
                suffix_pattern = f"___{parent_id}"
                parent_df = df[
                    df["hierarchy_node_id"].fillna("").str.endswith(suffix_pattern)
                ]
            if len(parent_df) == 0:
                break
            parent_order = parent_df.iloc[0]["order"]
            if parent_order is not None:
                global_parent_orders.add(parent_order)
            parent_id = parent_df.iloc[0].get("parent_id")

    # Track BOP-only header nodes we intentionally skip so we can promote descendants.
    bop_skipped_parent_ids: set[str] = set()

    def _track_skipped_parent_ids(row_like: dict[str, Any]) -> None:
        node_id = row_like.get("hierarchy_node_id")
        ind_code = row_like.get("indicator_code")
        for v in (node_id, ind_code):
            if not v:
                continue
            sv = str(v)
            bop_skipped_parent_ids.add(sv)
            if "___" in sv:
                bop_skipped_parent_ids.add(sv.rsplit("___", 1)[-1])

    def _lookup_parent_row(parent_id: str):
        parent_df = df[df["hierarchy_node_id"] == parent_id]
        if len(parent_df) == 0:
            suffix_pattern = f"___{parent_id}"
            parent_df = df[
                df["hierarchy_node_id"].fillna("").str.endswith(suffix_pattern)
            ]
        if len(parent_df) == 0 and "indicator_code" in df.columns:
            parent_df = df[df["indicator_code"] == parent_id]
        return parent_df

    def _promote_level_if_parent_skipped(level: int, parent_id: Any) -> int:
        adjusted = level
        pid = str(parent_id) if parent_id else ""
        while pid and pid in bop_skipped_parent_ids and adjusted > 0:
            adjusted -= 1
            parent_df = _lookup_parent_row(pid)
            if len(parent_df) == 0:
                break
            pid = str(parent_df.iloc[0].get("parent_id") or "")
        return adjusted

    # Track the last meaningful (non-BOP-only) header title at each level.
    # This is used to preserve qualifiers like "excluding exceptional financing"
    # for BOP suffix rows even when intermediate accounting-entry headers are skipped.
    last_meaningful_header_by_level: dict[int, str] = {}

    def _normalize_title(raw_title: str | None) -> str:
        title = (raw_title or "").lstrip()

        # Remove header marker (used for promoted headers in the rendered output)
        if title.startswith("▸"):
            title = title[1:].lstrip()

        # Strip parenthetical unit suffix
        if " (" in title and title.endswith(")"):
            paren_idx = title.rfind(" (")
            if paren_idx > 0:
                title = title[:paren_idx]

        # Strip common unit qualifiers that can trail titles
        unit_suffixes = [", Transactions", ", Stocks", ", Flows"]
        for suffix in unit_suffixes:
            if title.endswith(suffix):
                title = title[: -len(suffix)]
                break

        return title

    def _nearest_non_bop_ancestor_title(parent_id: Any) -> str | None:
        pid = str(parent_id) if parent_id else ""
        safety = 0
        while pid and safety < 50:
            safety += 1
            parent_df = _lookup_parent_row(pid)
            if len(parent_df) == 0:
                return None
            parent_first = parent_df.iloc[0]
            parent_title = _normalize_title(str(parent_first.get("title") or ""))
            if (
                parent_title
                and not is_bop_suffix_only(parent_title)
                and not parent_title.endswith((", Net", ", Credit", ", Debit"))
            ):
                return parent_title
            pid = str(parent_first.get("parent_id") or "")
        return None

    # OUTER LOOP: Iterate by sorted_orders (ITEM first)
    for order in sorted_orders:
        order_df = df[df["order"] == order]
        if order_df.empty:
            continue
        first = order_df.iloc[0]
        level = first["level"] or 0

        # Clear deeper header context when we move up the tree.
        for k in [k for k in last_meaningful_header_by_level if k > level]:
            del last_meaningful_header_by_level[k]

        is_header = first["is_category_header"]
        title = first["title"] or ""
        original_unit_suffix = ""

        # Strip parenthetical unit suffix
        if " (" in title and title.endswith(")"):
            paren_idx = title.rfind(" (")
            if paren_idx > 0:
                original_unit_suffix = title[paren_idx:]
                title = title[:paren_idx]

        unit_suffixes = [", Transactions", ", Stocks", ", Flows"]
        for suffix in unit_suffixes:
            if title.endswith(suffix):
                title = title[: -len(suffix)]
                break

        # Determine if this order should be rendered as a header
        is_promoted_header = (
            not is_header
            and order in global_parent_orders
            and order not in all_orders_with_data
        )
        # Only render as header if it doesn't have data of its own
        should_render_as_header = (
            is_header or is_promoted_header
        ) and order not in all_orders_with_data

        # Skip headers that don't lead to any data
        if should_render_as_header and order not in global_parent_orders:
            # If this is a BOP-only accounting-entry header (Net/Credit/Debit/etc.),
            # track it even when skipped for "no data" so descendants can be promoted.
            if is_bop_suffix_only(title):
                _track_skipped_parent_ids(first.to_dict())
            continue

        # Skip phantom BOP headers that are just "Net", "Credit", "Debit", etc.
        # Record them so descendants can be promoted (prevents Debit nesting under Credit
        # when an intermediate accounting-entry node is hidden).
        if should_render_as_header and is_bop_suffix_only(title):
            _track_skipped_parent_ids(first.to_dict())
            continue

        # If a row's parent (or higher ancestor) was skipped as a BOP-only header,
        # promote it so it doesn't appear as a child of the wrong visible node.
        level = _promote_level_if_parent_skipped(level, first.get("parent_id"))

        # ISORA: Only show topic headers
        if is_isora and should_render_as_header:
            if title and "___" in title:
                continue
            is_topic = bool(
                title
                and (
                    re.match(r"^\d+\.\s", title)
                    or "INDICATORS BY TOPIC" in title.upper()
                )
            )
            if not is_topic:
                continue

        # Headers get minimal simplification
        if should_render_as_header:
            if title.startswith("Financial corporations, "):
                title = title[len("Financial corporations, ") :]
            elif title.startswith("Depository corporations, "):
                title = title[len("Depository corporations, ") :]
        else:
            # Strip ancestor title prefixes
            best_prefix = hierarchy_ctx.find_best_prefix(order, title, parent_orders)
            if best_prefix and title.startswith(best_prefix):
                relative = title[len(best_prefix) :].lstrip(", :")
                # Don't strip if it would leave only a BOP suffix
                if (
                    relative
                    and title != best_prefix
                    and not is_bop_suffix_only(relative)
                ):
                    title = relative

            while True:
                best_suffix = hierarchy_ctx.find_best_suffix(
                    order, title, parent_orders
                )
                if best_suffix and title.endswith(best_suffix):
                    title = title[: -len(best_suffix)]
                else:
                    break

            while True:
                part_prefix = hierarchy_ctx.find_ancestor_part_prefix(
                    order, title, parent_orders
                )
                if part_prefix and title.startswith(part_prefix):
                    title = title[len(part_prefix) :]
                else:
                    break

        # Update header context for this level, or (for BOP suffix rows) inherit
        # the nearest meaningful header when the row's base is a strict prefix.
        if should_render_as_header:
            header_base = title.strip()
            if header_base and not is_bop_suffix_only(header_base):
                last_meaningful_header_by_level[level] = header_base
        else:
            for bop_suffix in (", Net", ", Credit", ", Debit"):
                if title.endswith(bop_suffix):
                    base = title[: -len(bop_suffix)].strip()
                    ancestor_title: str | None = None
                    for ancestor_level in range(level - 1, -1, -1):
                        cand = last_meaningful_header_by_level.get(ancestor_level)
                        if not cand:
                            continue
                        if cand.endswith((", Net", ", Credit", ", Debit")):
                            continue
                        ancestor_title = cand
                        break

                    if (
                        ancestor_title
                        and ancestor_title != base
                        and ancestor_title.startswith(base)
                    ):
                        title = f"{ancestor_title}{bop_suffix}"
                    break

        # Calculate indent
        extra_indent = "   " if should_add_table_header else ""
        indent = extra_indent + "   " * level

        prefix = "▸ " if should_render_as_header else "  "

        if should_render_as_header:
            if order in global_parent_orders:
                if is_isora and title and "___" in title:
                    continue

                header_title = title
                if has_uniform_unit_scale:
                    if level == 0 and uniform_suffix:
                        header_title += uniform_suffix
                elif original_unit_suffix:
                    header_title += original_unit_suffix

                # Check if this header order also has data
                order_data_rows = [dr for dr in data_rows if dr["order"] == order]
                if order_data_rows:
                    # Header WITH data - render data rows with header styling
                    order_dim_groups = order_to_dim_data.get(order, [])
                    if order_dim_groups and len(order_dim_groups[0][1]) > 1:
                        # Multiple dimension values - show header then dimension breakdown
                        row = {
                            "title": f"{indent}{prefix}{header_title}",
                            "country": "",
                        }
                        for d in dates:
                            row[str(d)] = ""
                        rows.append(row)
                        # Render dimension breakdown under header
                        for grouping_key, dim_data_rows in sorted(order_dim_groups):
                            if grouping_key:
                                dim_label = format_dim_labels(grouping_key)
                                for dr in dim_data_rows:
                                    dim_indent = extra_indent + "   " * (level + 1)
                                    row = {
                                        "title": f"{dim_indent}{dim_label}",
                                        "country": dr["country"],
                                    }
                                    row.update(dr["values"])
                                    rows.append(row)
                    else:
                        # Single or no dimension - show header row with its data
                        for dr in order_data_rows:
                            row = {
                                "title": f"{indent}{prefix}{header_title}",
                                "country": dr["country"],
                            }
                            row.update(dr["values"])
                            rows.append(row)
                else:
                    # Pure header - no data
                    row = {
                        "title": f"{indent}{prefix}{header_title}",
                        "country": "",
                    }
                    for d in dates:
                        row[str(d)] = ""
                    rows.append(row)
        else:
            # Data row - check if THIS specific order has multiple dimension values
            order_dim_groups = order_to_dim_data.get(order, [])
            # Has multi dims if there's more than one grouping key OR
            # if a single grouping key has multiple rows (multiple counterpart countries, etc.)
            order_has_multi_dims = len(order_dim_groups) > 1 or (
                len(order_dim_groups) == 1 and len(order_dim_groups[0][1]) > 1
            )

            if order_has_multi_dims:
                # Multiple dimension groups for this item - show breakdown
                data_level = level
                data_indent = extra_indent + "   " * data_level

                display_title = title
                if data_level == 0 and uniform_suffix and not should_add_table_header:
                    display_title += uniform_suffix
                elif not has_uniform_unit_scale:
                    # Get unit from first data row for this order
                    first_dr = order_dim_groups[0][1][0] if order_dim_groups else None
                    if first_dr:
                        row_unit_suffix = format_unit_suffix(
                            first_dr.get("unit"), first_dr.get("scale")
                        )
                        display_title += row_unit_suffix

                # Find "World" or top-level aggregate to show on parent row
                # World is typically code "G001" for COUNTERPART_COUNTRY dimension
                world_grouping_key = None
                world_data_row = None
                for gk, drs in order_dim_groups:
                    if gk:
                        for dim_id, code, label in gk:
                            if dim_id == "COUNTERPART_COUNTRY" and (
                                code == "G001" or label == "World"
                            ):
                                world_grouping_key = gk
                                world_data_row = drs[0] if drs else None
                                break
                    if world_grouping_key:
                        break

                # Item row - shows World data if available, otherwise empty
                item_row: dict[str, Any] = {
                    "title": f"{data_indent}{display_title}",
                    "country": world_data_row["country"] if world_data_row else "",
                }
                if world_data_row:
                    item_row.update(world_data_row["values"])
                else:
                    for d in dates:
                        item_row[str(d)] = ""
                rows.append(item_row)

                # Check if this is a COUNTERPART_COUNTRY breakdown
                has_counterpart_country = any(
                    dim_id == "COUNTERPART_COUNTRY"
                    for gk, _ in order_dim_groups
                    if gk
                    for dim_id, _, _ in gk
                )

                if has_counterpart_country:
                    # Separate groups from countries and order: groups first, then countries
                    cc_indent = extra_indent + "   " * (data_level + 1)

                    # Helper to detect if a code is a group vs individual country
                    # ISO country codes are 3 letters (e.g., USA, GBR, CHN)
                    # Group codes have letter+digit patterns (e.g., G001, GX225, U005, TX983)
                    def is_group_code(code: str) -> bool:
                        """Group codes have letter(s) followed by digits."""
                        # ISO codes are exactly 3 uppercase letters
                        if re.match(r"^[A-Z]{3}$", code):
                            return False
                        # Group codes: G###, GX###, U###, TX###
                        return bool(re.match(r"^[A-Z]+\d+$", code))

                    # Collect groups and individual countries separately
                    groups: list[tuple[tuple, list[dict], str, str]] = []
                    individual_countries: list[tuple[tuple, list[dict], str, str]] = []

                    for gk, drs in order_dim_groups:
                        if gk == world_grouping_key:
                            continue  # Skip World - already on parent
                        if gk:
                            cc_code = None
                            cc_label = None
                            for dim_id, code, label in gk:
                                if dim_id == "COUNTERPART_COUNTRY":
                                    cc_code = code
                                    cc_label = label
                                    break

                            if cc_label and cc_code:
                                if is_group_code(cc_code):
                                    groups.append((gk, drs, cc_label, cc_code))
                                else:
                                    individual_countries.append(
                                        (gk, drs, cc_label, cc_code)
                                    )

                    # Helper to get the max absolute value for sorting
                    def get_sort_value(item: tuple) -> float:
                        """Get the first numeric value from data rows for sorting."""
                        _, drs, _, _ = item
                        for dr in drs:
                            for v in dr.get("values", {}).values():
                                if v is not None:
                                    try:
                                        return abs(float(v))
                                    except (ValueError, TypeError):
                                        pass
                        return 0.0

                    # Render groups first (sorted by value, highest first),
                    # then countries (sorted by value, highest first)
                    for gk, drs, cc_label, cc_code in sorted(
                        groups, key=get_sort_value, reverse=True
                    ):
                        for dr in drs:
                            if all(d == 0 or d is None for d in dr["values"].values()):
                                continue  # Skip zero-value countries
                            row = {
                                "title": f"{cc_indent}▸ {cc_label}",
                                "country": dr["country"],
                            }
                            row.update(dr["values"])
                            rows.append(row)

                    for gk, drs, cc_label, cc_code in sorted(
                        individual_countries, key=get_sort_value, reverse=True
                    ):
                        for dr in drs:
                            if all(d == 0 or d is None for d in dr["values"].values()):
                                continue  # Skip zero-value countries
                            row = {
                                "title": f"{cc_indent}  {cc_label}",
                                "country": dr["country"],
                            }
                            row.update(dr["values"])
                            rows.append(row)
                else:
                    # Non-counterpart-country dimension breakdown (e.g., SECTOR)
                    for grouping_key, dim_data_rows in sorted(order_dim_groups):
                        if grouping_key == world_grouping_key:
                            continue
                        if grouping_key:
                            dim_label = format_dim_labels(grouping_key)
                            for dr in dim_data_rows:
                                sector_indent = extra_indent + "   " * (data_level + 1)
                                row = {
                                    "title": f"{sector_indent}  {dim_label}",
                                    "country": dr["country"],
                                }
                                row.update(dr["values"])
                                rows.append(row)
                        else:
                            for dr in dim_data_rows:
                                row = {
                                    "title": f"{data_indent}{display_title}",
                                    "country": dr["country"],
                                }
                                row.update(dr["values"])
                                rows.append(row)
            else:
                # Single dimension group - original behavior
                for dr in data_rows:
                    if dr["order"] == order:
                        # Use the already-corrected level (includes BOP overrides)
                        data_level = level
                        data_indent = extra_indent + "   " * data_level

                        # Use the stripped title (from BOP child processing above), not dr["title"]
                        display_title = title
                        if (
                            data_level == 0
                            and uniform_suffix
                            and not should_add_table_header
                        ):
                            display_title += uniform_suffix
                        elif not has_uniform_unit_scale:
                            row_unit_suffix = format_unit_suffix(
                                dr.get("unit"), dr.get("scale")
                            )
                            display_title += row_unit_suffix

                        row = {
                            "title": f"{data_indent}{display_title}",
                            "country": dr["country"],
                        }
                        row.update(dr["values"])
                        rows.append(row)

    result_df = pd.DataFrame(rows)
    result_df = result_df.set_index(["title", "country"])

    return result_df