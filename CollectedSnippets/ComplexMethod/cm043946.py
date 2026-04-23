def detect_indicator_dimensions(
    dataflow: str, indicator_codes: list[str], metadata
) -> dict[str, list[str]]:
    """
    Detect which dimension each indicator code belongs to.

    Different dataflows use different dimension names for indicators:
    - INDICATOR (most common)
    - BOP_ACCOUNTING_ENTRY (Balance of Payments)
    - SERIES (some datasets)
    - ITEM (some datasets)
    etc.

    Supports compound codes like 'HICP_CP01' which are split into multiple
    dimensions (e.g., INDEX_TYPE=HICP, COICOP_1999=CP01).

    Also supports compound codes with non-indicator dimensions like 'S13_G1_G23_T'
    which combines SECTOR + GFS_GRP + INDICATOR.

    Returns a dict mapping dimension_id -> list of indicator codes.

    Raises
    ------
    OpenBBError
        If any indicator code is not valid for the dataflow.
    """
    # pylint: disable=import-outside-toplevel
    from collections import defaultdict

    dimension_codes: dict[str, list[str]] = defaultdict(list)

    try:
        code_to_dimension, codes_by_dimension, dimension_order = (
            _build_dimension_lookups(dataflow, metadata)
        )

        invalid_codes: list[tuple[str, list[str]]] = []  # (code, unmatched_parts)
        for code in indicator_codes:
            if code == "*":
                # Handle wildcard - prefer INDICATOR dimension if available
                if "INDICATOR" in codes_by_dimension:
                    dimension_codes["INDICATOR"].append(code)
                elif code_to_dimension:
                    primary_dim = next(iter(code_to_dimension.values()))
                    dimension_codes[primary_dim].append(code)
                else:
                    dimension_codes["INDICATOR"].append(code)
            elif code in code_to_dimension:
                dimension_codes[code_to_dimension[code]].append(code)
            else:
                # Try to parse compound codes
                matched_parts, unmatched = _parse_compound_code(code, code_to_dimension)
                if matched_parts and not unmatched:
                    # All parts matched - valid compound code
                    for dim_id, code_part in matched_parts:
                        if code_part not in dimension_codes[dim_id]:
                            dimension_codes[dim_id].append(code_part)
                else:
                    # Either no matches or some parts didn't match
                    invalid_codes.append((code, unmatched))

        if invalid_codes:
            # Build detailed error message using dimension order
            error_parts: list[str] = []

            # Country-like dimensions to exclude unless explicitly matched
            country_dims = {"COUNTRY", "REF_AREA"}

            for code, unmatched in invalid_codes:
                if unmatched:
                    # First pass: identify all segments and their matches
                    parts = code.split("_")
                    segments: list[tuple[str, str | None]] = (
                        []
                    )  # (segment, dim_id or None)

                    i = 0
                    while i < len(parts):
                        # Try greedy matching (longest first)
                        matched = False
                        for j in range(len(parts), i, -1):
                            combined = "_".join(parts[i:j])
                            if combined in code_to_dimension:
                                segments.append((combined, code_to_dimension[combined]))
                                i = j
                                matched = True
                                break
                        if not matched:
                            segments.append((parts[i], None))
                            i += 1

                    # Check if any segment matched a country dimension
                    has_country_match = any(
                        dim_id in country_dims for _, dim_id in segments if dim_id
                    )

                    # Build effective dimension order - exclude country if not matched
                    effective_dim_order = (
                        dimension_order
                        if has_country_match
                        else [d for d in dimension_order if d not in country_dims]
                    )

                    # Find the first matched dimension to anchor our position
                    first_matched_idx: Any = None
                    first_matched_dim_pos: Any = None
                    for idx, (seg, dim_id) in enumerate(segments):  # type: ignore
                        if dim_id and dim_id in effective_dim_order:
                            first_matched_idx = idx
                            first_matched_dim_pos = effective_dim_order.index(dim_id)
                            break

                    # Build error messages
                    segment_errors: list = []
                    for idx, (seg, dim_id) in enumerate(segments):  # type: ignore
                        if dim_id is None:
                            # Calculate expected dimension based on position relative to first match
                            if (
                                first_matched_idx is not None
                                and first_matched_dim_pos is not None
                            ):
                                expected_pos = first_matched_dim_pos - (
                                    first_matched_idx - idx
                                )
                            else:
                                expected_pos = idx

                            if 0 <= expected_pos < len(effective_dim_order):
                                expected_dim = effective_dim_order[expected_pos]
                                sample = sorted(
                                    codes_by_dimension.get(expected_dim, set())
                                )[:5]
                                segment_errors.append(
                                    f"'{seg}' is invalid for {expected_dim} (valid: {', '.join(sample)})"
                                )
                            else:
                                segment_errors.append(f"'{seg}' is unrecognized")

                    error_parts.append(f"'{code}': {'; '.join(segment_errors)}")
                else:
                    error_parts.append(f"'{code}'")

            raise OpenBBError(
                f"Invalid indicator code(s) for dataflow '{dataflow}': "
                f"{'; '.join(error_parts)}. "
                f"Use `obb.economy.available_indicators(provider='imf', dataflows='{dataflow}')` to see all valid codes."
            )

    except OpenBBError:
        raise
    except Exception:
        # Fallback: put all codes in INDICATOR dimension (can't validate)
        dimension_codes["INDICATOR"] = indicator_codes

    return dict(dimension_codes)