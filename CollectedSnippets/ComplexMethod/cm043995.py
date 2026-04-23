def transform_data(
        query: CftcCotSearchQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[CftcCotSearchData]:
        """Transform the data."""
        results: list[CftcCotSearchData] = []
        seen: set[str] = set()
        for d in data:
            code = d.get("cftc_contract_market_code", "")
            if code and code not in seen:
                seen.add(code)
                name = d.get("commodity_name", "")

                if "commodity_group_name" not in list(
                    d
                ) and name.strip().upper().endswith("INDICES"):
                    category = "FINANCIAL INSTRUMENTS"
                    subcategory = "STOCK INDICES"
                    d["commodity_group_name"] = category
                    d["commodity_subgroup_name"] = subcategory
                elif (
                    "commodity_group_name" not in list(d)
                    and "CRYPTO" in name.strip().upper()
                ):
                    category = "FINANCIAL INSTRUMENTS"
                    subcategory = "DIGITAL ASSET (NON-MAJOR)"
                    d["commodity_group_name"] = category
                    d["commodity_subgroup_name"] = subcategory

                d["cftc_contract_market_code"] = f"CFTC_{code}"
                results.append(CftcCotSearchData.model_validate(d))

        return results