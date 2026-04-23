async def aextract_data(
        query: CboeEquityQuoteQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> "DataFrame":
        """Return the raw data from the Cboe endpoint."""
        # pylint: disable=import-outside-toplevel
        from openbb_cboe.utils.helpers import (
            TICKER_EXCEPTIONS,
            get_company_directory,
            get_index_directory,
        )
        from openbb_core.provider.utils.helpers import amake_requests
        from pandas import DataFrame, concat

        symbols = query.symbol.split(",")
        # First get the index and company directories so we know how to handle the ticker symbols.
        # Using cache for faster response times.
        SYMBOLS = await get_company_directory(use_cache=query.use_cache, **kwargs)
        INDEXES = await get_index_directory(use_cache=query.use_cache, **kwargs)
        INDEXES = INDEXES.set_index("index_symbol")

        # Create a list of European indices.
        EU_INDEXES = INDEXES[INDEXES["source"] == "eu_proprietary_index"]

        # Check all symbols and create a list of URLs to request.
        urls = []
        for symbol in symbols:
            base_url = "https://cdn.cboe.com/api/global/delayed_quotes/quotes/"
            url = (
                f"{base_url}_{symbol.replace('^', '')}.json"
                if symbol.replace("^", "") in INDEXES.index
                or symbol.replace("^", "") in TICKER_EXCEPTIONS
                else f"{base_url}{symbol.replace('^', '')}.json"
            )
            # European Indices require a different endpoint.
            if symbol in EU_INDEXES.index:
                eu_name = EU_INDEXES.at[symbol, "name"]
                _symbol = EU_INDEXES[EU_INDEXES["name"].str.contains(eu_name)].index[0]
                url = (
                    "https://cdn.cboe.com/api/global/european_indices/"
                    + f"index_quotes/{_symbol.replace('^', '')}.json"
                )
            urls.append(url)
        # Now make the requests.
        responses = await amake_requests(urls)
        if not responses:
            raise EmptyDataError()
        quotes_data = [d["data"] for d in responses]
        # There is no context for this data so we'll remove it.
        [d.pop("seqno") for d in quotes_data if "seqno" in d]
        [d.pop("exchange_id") for d in quotes_data if "exchange_id" in d]

        quotes = DataFrame(quotes_data)
        quotes.symbol = quotes.symbol.str.replace("^", "")
        quotes.symbol = [s.split("-")[0] for s in quotes.symbol]
        # Drop an additional symbol column from EU Indices.
        if "index" in quotes.columns:
            quotes = quotes.drop(columns="index")
        quotes = DataFrame(quotes).set_index("symbol")

        # Now get the URLs for the IV data.
        base_url = "https://cdn.cboe.com/api/global/delayed_quotes/historical_data/"
        iv_urls = []
        for symbol in symbols:
            iv_url = (
                base_url + f"_{symbol.replace('^', '')}.json"
                if symbol.replace("^", "") in TICKER_EXCEPTIONS
                or symbol.replace("^", "") in INDEXES.index
                else base_url + f"{symbol.replace('^', '')}.json"
            )
            # There is no IV data for the EU Indices, so we'll skip those symbols.
            if symbol not in EU_INDEXES.index:
                iv_urls.append(iv_url)

            # While iterating through the symbols, grab the name belonging to the ticker.
            if symbol.replace("^", "") in SYMBOLS.index:
                quotes.loc[symbol.replace("^", ""), "name"] = SYMBOLS.loc[
                    symbol.replace("^", ""), "name"
                ]
            if symbol.replace("^", "") in INDEXES.index:
                quotes.loc[symbol.replace("^", ""), "name"] = INDEXES.loc[
                    symbol.replace("^", ""), "name"
                ]
            if symbol.replace("^", "") in EU_INDEXES.index:
                quotes.loc[symbol.replace("^", ""), "name"] = EU_INDEXES.loc[
                    symbol.replace("^", ""), "name"
                ]

        # Now get the IV data.
        iv = DataFrame()
        iv_responses = await amake_requests(iv_urls)
        if iv_responses:
            iv_data = [d["data"] for d in iv_responses]
            iv = DataFrame(iv_data)
            iv["symbol"] = iv["symbol"].astype(str).str.replace("^", "")
            iv = iv.set_index("symbol")
        if not iv_responses:
            iv = DataFrame()

        # Merge the IV data with the quotes data.
        results = concat([quotes, iv], axis=1)

        if len(results) == 0:
            raise EmptyDataError()
        return results