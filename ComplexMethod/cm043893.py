def transform_data(
        query: ImfConsumerPriceIndexQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> AnnotatedResult[list[ImfConsumerPriceIndexData]]:
        """Transform data and validate the model."""
        row_data = data.get("data", [])
        result: list[ImfConsumerPriceIndexData] = []
        metadata: dict = data.get("metadata", {})
        dataset_info: dict = metadata.pop("dataset", {})
        table_info: dict = (
            metadata.pop("IMF_STA_CPI_CPI", {})
            or metadata.pop("IMF_STA_CPI_HICP", {})
            or {}
        )
        dataset_info["index_type"] = table_info.get("indicator", "")
        dataset_info["index_description"] = table_info.get("description", "")

        if not row_data:
            raise OpenBBError("No data returned for the given query parameters.")

        for item in row_data:
            # Filter by date range here because IMF API date filtering can be inconsistent
            item_date = item.get("TIME_PERIOD", None)
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

            # Get translated labels (these are now human-readable)
            frequency = (item.get("FREQUENCY") or "").strip()
            index_type = (item.get("INDEX_TYPE") or "").strip()
            expenditure = (item.get("COICOP_1999") or item.get("title") or "").strip()
            expenditure_code = (item.get("COICOP_1999_code") or "").strip()
            transformation = (item.get("TYPE_OF_TRANSFORMATION") or "").strip()
            # Build title from translated values
            title = f"{frequency} {index_type} - {expenditure} - {transformation}"
            # Get unit from transformation (use last part if comma-separated)
            unit = (transformation.rsplit(", ", maxsplit=1)[-1] or "").strip()
            # Get sort order from expenditure code
            order = expenditure_order.get(expenditure_code, 99)
            obs_value = item.get("OBS_VALUE", None)
            multiplier = item.get("UNIT_MULT", 1)

            if "percent" in unit.lower() and obs_value is not None:
                obs_value = obs_value / 100.0
                multiplier = 100
            symbol = item.get("series_id", "").strip().split("IMF_STA_CPI_")[-1]
            symbol = f"CPI::{symbol}"
            new_row = {
                "date": item_date,
                "country": (item.get("COUNTRY") or "").strip() or None,
                "country_code": (item.get("country_code") or "").strip() or None,
                "series_id": symbol,
                "expenditure": expenditure or None,
                "title": title.strip(),
                "unit": unit,
                "unit_multiplier": multiplier,
                "value": obs_value,
                "order": order,
            }
            result.append(ImfConsumerPriceIndexData.model_validate(new_row))

        # Sort by date, then country, then order (expenditure)
        result.sort(
            key=lambda x: (
                x.date,
                x.country or "",
                x.order if x.order is not None else 99,
            )
        )

        return AnnotatedResult(
            result=result, metadata={"dataset": dataset_info, "series": metadata}
        )