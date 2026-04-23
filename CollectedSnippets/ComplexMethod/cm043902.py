def transform_data(
        query: ImfEconomicIndicatorsQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> AnnotatedResult[list[ImfEconomicIndicatorsData]]:
        """Transform the data."""
        mode = data.get("mode", "indicator")
        row_data = data.get("data", [])

        if not row_data:
            raise EmptyDataError("No data returned for the given query parameters.")

        result: list = []
        metadata: dict = {}

        if mode == "table":
            metadata = {
                "table": data.get("table_metadata", {}),
                "series": data.get("series_metadata", {}),
            }
        else:
            metadata = data.get("metadata", {})

        for item in row_data:
            # Filter by date range if needed (IMF API date filtering can be inconsistent)
            item_date = item.get("TIME_PERIOD") or item.get("date")

            # Normalize date format for comparison and storage
            if item_date:
                item_date = parse_time_period(item_date)

            if (
                query.start_date
                and item_date
                and item_date < query.start_date.strftime("%Y-%m-%d")
            ):
                continue
            if (
                query.end_date
                and item_date
                and item_date > query.end_date.strftime("%Y-%m-%d")
            ):
                continue

            # Extract indicator code from various possible fields
            symbol = (
                item.get("series_id")  # Prefer full series_id (dataflow::codes)
                or item.get("INDICATOR_code")
                or item.get("BOP_ACCOUNTING_ENTRY_code")
                or item.get("SERIES_code")
                or item.get("ITEM_code")
                or item.get("indicator_code")
                or item.get("symbol")
            )
            # Get country info (ISORA uses JURISDICTION instead of COUNTRY)
            country = (
                item.get("COUNTRY") or item.get("JURISDICTION") or item.get("country")
            )
            country_code = (
                item.get("country_code")
                or item.get("COUNTRY_code")
                or item.get("JURISDICTION_code")
            )
            # Get hierarchy info (for table mode)
            order = item.get("order")
            level = item.get("level")
            parent_id = item.get("parent_id")
            is_category_header = item.get("is_category_header", False)
            # Get title/label - use the title from table_builder which is the indicator name
            # For data rows, this is the specific indicator (e.g., "Direct investment, Equity...")
            # For headers, this is the category name with units (e.g., "Goods (Millions, US Dollar)")
            title = item.get("title") or item.get("INDICATOR") or item.get("label")
            # Get value - use explicit None check to handle 0 correctly
            value = item.get("OBS_VALUE")

            if value is None:
                value = item.get("value")

            # Sanitize scale - convert nan/None to None, ensure string type
            scale_val = item.get("scale") or item.get("SCALE")
            if scale_val is not None:
                if str(scale_val).lower() == "nan":
                    scale_val = None
                elif not isinstance(scale_val, str):
                    scale_val = str(scale_val) if scale_val else None

            # Sanitize unit - convert nan/None to None, ensure string type
            unit_val = (
                item.get("unit")
                or item.get("UNIT")
                or item.get("TYPE_OF_TRANSFORMATION")
            )
            if unit_val is not None:
                if str(unit_val).lower() == "nan":
                    unit_val = None
                elif not isinstance(unit_val, str):
                    unit_val = str(unit_val) if unit_val else None

            new_row = {
                "date": item_date,
                "symbol": symbol,
                "country": country,
                "country_code": country_code,
                "value": value,
                "unit": unit_val,
                "unit_multiplier": item.get("unit_multiplier") or item.get("UNIT_MULT"),
                "scale": scale_val,
                "order": order,
                "level": level,
                "symbol_root": parent_id,  # Map to symbol_root for base class
                "parent_id": parent_id,  # Also keep as parent_id
                "parent_code": item.get(
                    "parent_code"
                ),  # Resolved parent indicator code
                "hierarchy_node_id": item.get(
                    "hierarchy_node_id"
                ),  # Hierarchy node ID for parent tracing
                "title": title,
                "description": item.get("description"),
                "series_id": item.get("series_id"),
                "is_category_header": is_category_header,
            }

            # Dynamically add ALL dimension fields from the raw data
            # This captures any dimension like SECTOR, PRICE_TYPE, DV_TYPE,
            # COUNTERPART_COUNTRY, etc. with both label and code
            for key, val in item.items():
                # Skip fields we've already handled
                if key in new_row:
                    continue
                # Skip internal/metadata fields
                if key in {
                    "TIME_PERIOD",
                    "OBS_VALUE",
                    "value",
                    "indicator_codes",
                    "COUNTRY",
                    "country_code",
                    "SCALE",
                    "UNIT",
                    "unit_multiplier",
                }:
                    continue
                # Include dimension fields (UPPERCASE) and their _code variants
                if key.isupper() or key.endswith("_code"):
                    # Convert to snake_case for the field name
                    field_name = key.lower()
                    new_row[field_name] = val

            result.append(new_row)

        # Check if all records were filtered out
        if not result:
            raise EmptyDataError(
                "No data remaining after applying date filters. "
                "Try adjusting start_date and end_date parameters."
            )

        result.sort(
            key=lambda x: (
                x["order"] if x.get("order") is not None else 9999,
                x["date"] if x.get("date") else "",
                x["country"] or "",
            )
        )
        to_exclude = [
            "is_category_header",
            "hierarchy_node_id",
            "parent_id",
            "indicator_code",
            "parent_code",
            "series_id",
        ]
        # Non-pivot mode: return flat list
        if not query.pivot:
            new_data: list = []
            for row in result:
                if not row.get("date"):
                    continue
                # Exclude internal fields
                row["symbol"] = row.get("series_id")
                for field in to_exclude:
                    _ = row.pop(field, None)
                new_data.append(ImfEconomicIndicatorsData.model_validate(row))

            return AnnotatedResult(
                result=new_data,
                metadata=metadata,
            )

        # Pivot mode: use the table_presentation utility module
        # pylint: disable=import-outside-toplevel
        from openbb_imf.utils.table_presentation import pivot_table_data

        result_df = pivot_table_data(
            result=result,
            country=query.country,  # type: ignore
            limit=query.limit,
            metadata=metadata,
        )
        result_df = result_df.fillna(0).reset_index()

        return AnnotatedResult(
            result=[
                ImfEconomicIndicatorsData.model_validate(r)
                for r in result_df.to_dict(orient="records")
            ],
            metadata=metadata,
        )