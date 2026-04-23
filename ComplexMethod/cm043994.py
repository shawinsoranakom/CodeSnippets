async def aextract_data(
        query: CftcCotSearchQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Search CFTC Commitment of Traders Reports via the live API."""
        # pylint: disable=import-outside-toplevel
        from urllib.parse import quote

        from openbb_cftc.utils import reports_dict
        from openbb_core.provider.utils.helpers import amake_request

        app_token = credentials.get("cftc_app_token") if credentials else ""

        report_type = query.report_type.replace("financial", "tff")
        if query.futures_only is True and report_type != "supplemental":
            report_type += "_futures_only"
        elif query.futures_only is False and report_type != "supplemental":
            report_type += "_combined"

        dataset_id = reports_dict[report_type]
        select_cols = (
            "cftc_contract_market_code,"
            "contract_market_name,"
            "commodity_name,"
            "commodity_group_name,"
            "commodity_subgroup_name,"
            "contract_units"
        )
        base_url = (
            f"https://publicreporting.cftc.gov/resource/{dataset_id}.json"
            f"?$select={select_cols}"
            f"&$group={select_cols}"
            "&$limit=50000"
            "&$order=commodity_group_name,commodity_subgroup_name,contract_market_name"
        )

        search_term = query.query
        where_parts: list[str] = []

        from datetime import datetime, timedelta

        cutoff = (datetime.now() - timedelta(weeks=52)).strftime("%Y-%m-%d")
        where_parts.append(f"Report_Date_as_YYYY_MM_DD > '{cutoff}'")

        if search_term:
            escaped = search_term.replace("'", "''")
            where_parts.append(
                f"(UPPER(contract_market_name) like UPPER('%{escaped}%')"
                f" OR UPPER(cftc_contract_market_code) like UPPER('%{escaped}%')"
                f" OR UPPER(commodity_name) like UPPER('%{escaped}%')"
                f" OR UPPER(commodity_group_name) like UPPER('%{escaped}%')"
                f" OR UPPER(commodity_subgroup_name) like UPPER('%{escaped}%'))"
            )

        if query.category:
            cat = query.category.replace("_", " ").upper()
            where_parts.append(f"UPPER(commodity_group_name) = '{cat}'")

        if query.subcategory:
            subcategory_map = {
                "currency_non_major": "CURRENCY(NON-MAJOR)",
                "digital_asset_non_major": "DIGITAL ASSET (NON-MAJOR)",
                "foodstuffs_softs": "FOODSTUFFS/SOFTS",
                "interest_rates_non_us_treasury": "INTEREST RATES - NON U.S. TREASURY",
                "interest_rates_us_treasury": "INTEREST RATES - U.S. TREASURY",
                "livestock_meat_products": "LIVESTOCK/MEAT PRODUCTS",
                "oilseed_and_products": "OILSEED AND PRODUCTS",
            }
            sub = subcategory_map.get(
                query.subcategory,
                query.subcategory.replace("_", " ").upper(),
            )
            where_parts.append(f"UPPER(commodity_subgroup_name) = '{sub}'")

        if where_parts:
            base_url += "&$where=" + quote(" AND ".join(where_parts))

        url = f"{base_url}&$$app_token={app_token}" if app_token else base_url

        try:
            response = await amake_request(url, **kwargs)
        except OpenBBError as error:
            raise error from error

        if not response:
            raise EmptyDataError(
                f"No results found for '{search_term}'."
                if search_term
                else "No results returned from the CFTC API."
            )

        return response