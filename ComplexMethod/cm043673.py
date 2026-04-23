def transform_data(
        query: IntrinioBalanceSheetQueryParams, data: list[dict], **kwargs: Any
    ) -> list[IntrinioBalanceSheetData]:
        """Return the transformed data."""
        transformed_data: list[IntrinioBalanceSheetData] = []
        period = "FY" if query.period == "annual" else "QTR"
        units = []
        for item in data:
            sub_dict: dict[str, Any] = {}

            for sub_item in item["financials"]:
                field_name = sub_item["data_tag"]["tag"]
                unit = sub_item["data_tag"].get("unit", "")
                if unit and len(unit) == 3:
                    units.append(unit)
                sub_dict[field_name] = (
                    float(sub_item["value"])
                    if sub_item["value"] and sub_item["value"] != 0
                    else None
                )

            sub_dict["period_ending"] = item["period_ending"]
            sub_dict["fiscal_year"] = item["fiscal_year"]
            sub_dict["fiscal_period"] = item["fiscal_period"]
            sub_dict["reported_currency"] = list(set(units))[0]

            # Intrinio does not return Q4 data but FY data instead
            if period == "QTR" and item["fiscal_period"] == "FY":
                sub_dict["fiscal_period"] = "Q4"

            transformed_data.append(IntrinioBalanceSheetData(**sub_dict))

        return transformed_data