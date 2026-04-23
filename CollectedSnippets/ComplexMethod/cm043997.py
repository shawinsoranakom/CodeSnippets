def transform_data(
        query: CftcCotQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[CftcCotData]:
        """Transform and validate the data."""
        response = data.copy()
        string_cols = [
            "market_and_exchange_names",
            "cftc_contract_market_code",
            "cftc_market_code",
            "cftc_region_code",
            "cftc_commodity_code",
            "cftc_contract_market_code_quotes",
            "cftc_market_code_quotes",
            "cftc_commodity_code_quotes",
            "cftc_subgroup_code",
            "commodity_group_name",
            "commodity",
            "commodity_name",
            "commodity_subgroup_name",
            "contract_units",
            "yyyy_report_week_ww",
            "id",
            "futonly_or_combined",
        ]
        results: list[CftcCotData] = []
        for values in response:
            new_values: dict = {}
            for key, value in values.items():
                if key == "report_date_as_yyyy_mm_dd" and value:
                    new_values["report_date_as_yyyy_mm_dd"] = value.split("T")[0]
                elif key in string_cols and value:
                    v = str(value)
                    if key == "contract_units":
                        v = v.strip("()")
                    new_values[key.lower()] = v
                elif key.lower().startswith("pct_") and value:
                    new_values[key.lower().replace("__", "_")] = float(value) / 100
                elif key.lower().startswith("conc_") and value:
                    new_values[key.lower().replace("__", "_")] = float(value)
                elif value:
                    try:
                        new_values[key.lower().replace("__", "_")] = int(value)
                    except ValueError:
                        new_values[key.lower().replace("__", "_")] = value

            if new_values:
                results.append(CftcCotData.model_validate(new_values))

        if results:
            dup_fields: set[str] = set()
            sample = results[0].model_dump()
            for fname in list(sample):
                base: str | None = None
                if fname.endswith("_old") or fname.endswith("_other"):
                    base = fname.rsplit("_", 1)[0] + "_all"
                elif fname.endswith("_1") or fname.endswith("_2"):
                    base = fname[:-2]
                if base is None or base not in sample:
                    continue
                pairs = [
                    (getattr(r, base, None), getattr(r, fname, None)) for r in results
                ]
                paired = [(a, b) for a, b in pairs if a is not None and b is not None]
                if paired and all(a == b for a, b in paired):
                    dup_fields.add(fname)
            if dup_fields:
                for r in results:
                    for col in dup_fields:
                        object.__setattr__(r, col, None)

        measure = query.measure
        if measure != "all" and results:
            _metadata = {
                "market_and_exchange_names",
                "cftc_contract_market_code",
                "cftc_market_code",
                "cftc_region_code",
                "cftc_commodity_code",
                "cftc_contract_market_code_quotes",
                "cftc_market_code_quotes",
                "cftc_commodity_code_quotes",
                "cftc_subgroup_code",
                "commodity",
                "commodity_group",
                "commodity_subgroup",
                "futonly_or_combined",
                "contract_units",
                "contract_market_name",
                "report_week",
                "id",
            }
            measure_prefixes = {
                "changes": "change_",
                "percent_of_oi": "open_interest_pct_",
                "traders": "traders_",
                "concentration": "concentration_",
            }

            def _keep(field_name: str) -> bool:
                if field_name in ("date", "open_interest_all"):
                    return True
                if field_name in _metadata:
                    return False
                if measure == "positions":
                    return not any(
                        field_name.startswith(p) for p in measure_prefixes.values()
                    )
                return field_name.startswith(measure_prefixes[measure])

            keep_fields = {
                f
                for r in results
                for f, v in r.model_dump().items()
                if _keep(f) and v is not None and v != 0
            }
            keep_fields.add("date")
            keep_fields.add("open_interest_all")

            filtered: list[CftcCotData] = []
            for r in results:
                d = {k: v for k, v in r.model_dump().items() if k in keep_fields}
                filtered.append(CftcCotData.model_validate(d))
            results = filtered

        results.sort(key=lambda r: r.date)
        if query.limit is not None and query.limit > 0:
            results = results[-query.limit :]

        return results