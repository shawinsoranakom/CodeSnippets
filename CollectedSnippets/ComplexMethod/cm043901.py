async def aextract_data(
        query: ImfEconomicIndicatorsQueryParams,
        credentials: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict:
        """Extract the data."""
        # pylint: disable=import-outside-toplevel
        from datetime import datetime  # noqa
        from openbb_imf.utils.query_builder import ImfQueryBuilder
        from openbb_imf.utils.table_builder import ImfTableBuilder

        countries = query.country.split(",")  # type: ignore
        countries_str = "+".join([c.upper() for c in countries])
        frequency_map = {"annual": "A", "quarter": "Q", "month": "M", "day": "D"}
        frequency = frequency_map.get(query.frequency) or query.frequency  # type: ignore
        start_date = query.start_date.strftime("%Y-%m-%d") if query.start_date else None
        end_date = query.end_date.strftime("%Y-%m-%d") if query.end_date else None

        # Parse dimension_values into a dict of DIM_ID -> DIM_VALUE
        # Input format: list of "DIM_ID:VALUE" strings
        # Example: ["SECTOR:S13", "GFS_GRP:XDC"] -> {"SECTOR": "S13", "GFS_GRP": "XDC"}
        # Handles lowercase inputs: "unit:xdc" -> {"UNIT": "XDC"}
        extra_dimensions: dict[str, str] = {}
        if query.dimension_values:
            for dv in query.dimension_values:
                # Each dv should be "DIMENSION:VALUE"
                if not dv or not isinstance(dv, str):
                    continue
                # Handle comma-separated pairs in a single string
                pairs = [p.strip() for p in dv.split(",") if p.strip()]
                for pair in pairs:
                    if ":" in pair:
                        dim_id, dim_value = pair.split(":", 1)
                        # Uppercase both dimension ID and value for IMF API
                        extra_dimensions[dim_id.strip().upper()] = (
                            dim_value.strip().upper()
                        )

        if query._is_table:
            # Table mode: use ImfTableBuilder (single dataflow only)
            dataflow = query._dataflow
            if not dataflow:
                raise OpenBBError("Could not determine dataflow from symbol.")

            params: dict[str, Any] = {
                "COUNTRY": countries_str,
                "FREQUENCY": frequency,
            }

            # Handle special dimensions for certain dataflows
            # GFS dataflows: GFS_BS, GFS_SOO, GFS_COFOG, GFS_SFCP, GFS_SSUC, QGFS
            if dataflow.startswith("GFS_") or dataflow == "QGFS":
                params["SECTOR"] = "*"
                params["GFS_GRP"] = "*"
            elif dataflow.startswith("FSIC") or dataflow == "IRFCL":
                params["SECTOR"] = "*"
            elif dataflow.startswith("BOP") or dataflow == "DIP":
                params["TYPE_OF_TRANSFORMATION"] = "*"
            elif dataflow == "ISORA_LATEST_DATA_PUB":
                params["INDICATOR"] = "*"

            # Apply user-specified dimension filters (overrides defaults above)
            if extra_dimensions:
                params.update(extra_dimensions)

            # Handle transform/unit for table mode
            if query.transform:
                transform_val = query.transform.strip().lower()
                transform_dim, unit_dim, transform_lookup, unit_lookup = (
                    detect_transform_dimension(dataflow)
                )
                applied = False
                resolved_code = None

                # Try transform dimension first
                if transform_dim:
                    if transform_val in ("all", "*"):
                        params[transform_dim] = "*"
                        applied = True
                    elif transform_val in transform_lookup:
                        resolved_code = transform_lookup[transform_val]
                        params[transform_dim] = resolved_code
                        applied = True

                # Try unit dimension if not applied to transform
                if not applied and unit_dim:
                    if transform_val in ("all", "*"):
                        params[unit_dim] = "*"
                        applied = True
                    elif transform_val in unit_lookup:
                        resolved_code = unit_lookup[transform_val]
                        params[unit_dim] = resolved_code
                        applied = True

                # Raise error if transform value is not valid for dataflow
                if not applied:
                    available = []
                    if transform_lookup:
                        available.extend(
                            sorted(
                                set(transform_lookup.keys())
                                - set(transform_lookup.values())
                            )
                        )
                    if unit_lookup:
                        available.extend(
                            sorted(set(unit_lookup.keys()) - set(unit_lookup.values()))
                        )
                    if not transform_dim and not unit_dim:
                        raise OpenBBError(
                            f"Dataflow '{dataflow}' does not support transform/unit parameter."
                        )
                    raise OpenBBError(
                        f"Invalid transform value '{query.transform}' for dataflow '{dataflow}'. "
                        f"Available options: {', '.join(available) if available else 'none'}"
                    )

            # We request one extra period to ensure value carry-forward for STATUS="NA" obs.
            if query.limit is not None and start_date is None:
                current_year = datetime.now().year
                if frequency == "A":
                    start_year = current_year - query.limit - 1
                    start_date = str(start_year)  # Just year for annual
                elif frequency == "Q":
                    years_back = (query.limit + 7) // 4 + 1
                    start_year = current_year - years_back
                    start_date = str(start_year)
                elif frequency == "M":
                    years_back = (query.limit + 23) // 12 + 1
                    start_year = current_year - years_back
                    start_date = str(start_year)

            table_builder = ImfTableBuilder()

            try:
                result = table_builder.get_table(
                    dataflow=dataflow,
                    table_id=query._table_id,
                    start_date=start_date,
                    end_date=end_date,
                    **params,
                )
                return {
                    "mode": "table",
                    "data": result.get("data", []),
                    "table_metadata": result.get("table_metadata", {}),
                    "series_metadata": result.get("series_metadata", {}),
                }
            except (ValueError, OpenBBError) as e:
                # Translate IMF dimension codes to user-friendly parameter names
                raise OpenBBError(translate_error_message(str(e))) from e

        else:
            # Indicator mode: support multiple dataflows
            query_builder = ImfQueryBuilder()
            all_data: list[dict] = []
            all_metadata: dict = {}
            indicators_by_df = query._indicators_by_dataflow

            if not indicators_by_df:
                raise OpenBBError("No indicators specified.")

            # Fetch data for each dataflow
            for dataflow, indicator_codes in indicators_by_df.items():
                params = {
                    "COUNTRY": countries_str,
                    "FREQUENCY": frequency,
                }

                # Apply user-specified dimension filters
                if extra_dimensions:
                    params.update(extra_dimensions)

                # Handle transform/unit parameter per dataflow
                if query.transform:
                    transform_val = query.transform.strip().lower()
                    transform_dim, unit_dim, transform_lookup, unit_lookup = (
                        detect_transform_dimension(dataflow)
                    )
                    applied = False
                    resolved_code = None

                    # Try transform dimension first
                    if transform_dim:
                        if transform_val in ("all", "*"):
                            params[transform_dim] = "*"
                            applied = True
                        elif transform_val in transform_lookup:
                            resolved_code = transform_lookup[transform_val]
                            params[transform_dim] = resolved_code
                            applied = True

                    # Try unit dimension if not applied to transform
                    if not applied and unit_dim:
                        if transform_val in ("all", "*"):
                            params[unit_dim] = "*"
                            applied = True
                        elif transform_val in unit_lookup:
                            resolved_code = unit_lookup[transform_val]
                            params[unit_dim] = resolved_code
                            applied = True

                    # Raise error if transform value is not valid for dataflow
                    if not applied:
                        available = []
                        if transform_lookup:
                            available.extend(
                                sorted(
                                    set(transform_lookup.keys())
                                    - set(transform_lookup.values())
                                )
                            )
                        if unit_lookup:
                            available.extend(
                                sorted(
                                    set(unit_lookup.keys()) - set(unit_lookup.values())
                                )
                            )
                        if not transform_dim and not unit_dim:
                            raise OpenBBError(
                                f"Dataflow '{dataflow}' does not support transform/unit parameter."
                            )
                        raise OpenBBError(
                            f"Invalid transform value '{query.transform}' for dataflow '{dataflow}'. "
                            f"Available options: {', '.join(available) if available else 'none'}"
                        )

                if query.limit is not None:
                    params["lastNObservations"] = query.limit

                # Detect indicator dimensions for this dataflow
                dimension_codes = detect_indicator_dimensions(
                    dataflow, indicator_codes, query_builder.metadata
                )

                # Add indicator codes to appropriate dimensions
                for dim_id, codes in dimension_codes.items():
                    params[dim_id] = "+".join(codes)

                try:
                    result = query_builder.fetch_data(
                        dataflow=dataflow,
                        start_date=start_date,
                        end_date=end_date,
                        **params,
                    )
                    # Add dataflow info to each record
                    for record in result.get("data", []):
                        record["_dataflow"] = dataflow
                    all_data.extend(result.get("data", []))
                    all_metadata[dataflow] = result.get("metadata", {})
                except ValueError as e:
                    # Translate IMF codes to user-friendly names and raise as OpenBBError
                    raise OpenBBError(translate_error_message(str(e))) from e

            return {
                "mode": "indicator",
                "data": all_data,
                "metadata": all_metadata,
            }