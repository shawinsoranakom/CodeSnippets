async def aextract_data(
        query: FMPGovernmentTradesQueryParams,
        credentials: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the Government Trades endpoint."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from openbb_core.app.model.abstract.error import OpenBBError
        from openbb_core.provider.utils.errors import EmptyDataError
        from openbb_core.provider.utils.helpers import amake_request
        from openbb_fmp.utils.helpers import response_callback
        from warnings import warn

        symbols: list = []

        if query.symbol:
            symbols = query.symbol.split(",")

        results: list[dict] = []
        chamber_url_dict = {
            "house": ["house-trades"],
            "senate": ["senate-trades"],
            "all": ["house-trades", "senate-trades"],
        }
        api_key = credentials.get("fmp_api_key") if credentials else ""
        keys_to_remove = {
            "district",
            "capitalGainsOver200USD",
            "disclosureYear",
            "firstName",
            "lastName",
        }
        keys_to_rename = {"dateReceived": "date", "disclosureDate": "date"}

        async def get_one(url):
            """Get data for one URL."""
            result = await amake_request(
                url, response_callback=response_callback, **kwargs
            )
            processed_list: list = []

            for entry in result:
                new_entry = {
                    keys_to_rename.get(k, k): v
                    for k, v in entry.items()
                    if k not in keys_to_remove
                }
                new_entry["chamber"] = "Senate" if "senate-trades" in url else "House"
                processed_list.append(new_entry)

            if not processed_list or len(processed_list) == 0:
                warn(f"No data found for {url.replace(api_key, 'API_KEY')}")

            if processed_list:
                results.extend(processed_list)

        urls_list: list = []
        base_url = "https://financialmodelingprep.com/stable/"
        limit = query.limit if query.limit else 1000
        try:
            if symbols:
                for symbol in symbols:
                    query.symbol = symbol
                    url = [
                        f"{base_url}{i}?symbol={symbol}&apikey={api_key}"
                        for i in chamber_url_dict[query.chamber]
                    ]
                    urls_list.extend(url)
                await asyncio.gather(*[get_one(url) for url in urls_list])
            else:
                page = 0
                seen = set()
                unique_results: list = []

                while len(unique_results) < limit:
                    all_urls = []
                    for i in chamber_url_dict[query.chamber]:
                        chamber = i.split("-")[0]
                        page_url = f"{base_url}{i.replace('trades', 'latest')}?page={page}&limit=250&apikey={api_key}"
                        all_urls.append((page_url, chamber.title()))

                    async def fetch_page(url_info):
                        url, chamber_name = url_info
                        try:
                            result = await amake_request(
                                url, response_callback=response_callback, **kwargs
                            )
                            if result:
                                for d in result:
                                    d["chamber"] = chamber_name
                                return result
                        except Exception:
                            return []
                        return []

                    page_results = await asyncio.gather(
                        *[fetch_page(url_info) for url_info in all_urls],
                        return_exceptions=True,
                    )

                    new_data_found = False
                    for page_result in page_results:
                        if isinstance(page_result, list) and page_result:
                            new_data_found = True
                            for d in page_result:
                                fs = frozenset(d.items())
                                if fs not in seen:
                                    seen.add(fs)
                                    unique_results.append(d)
                                    if len(unique_results) >= limit:
                                        break
                            if len(unique_results) >= limit:
                                break

                    if not new_data_found:
                        break  # No more data from any source
                    page += 1

                results = unique_results

            if not results:
                raise EmptyDataError("No data returned for the given symbol.")

            return results
        except OpenBBError as e:
            raise e from e