async def aextract_data(  # pylint: disable=R0914.R0912,R0915
        query: EconDbEconomicIndicatorsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Extract the data."""
        # pylint: disable=import-outside-toplevel
        from openbb_econdb.utils import helpers
        from openbb_econdb.utils.main_indicators import get_main_indicators

        if query.symbol.upper() == "MAIN":
            country = query.country.upper() if query.country else "US"

            return await get_main_indicators(
                country,
                query.start_date.strftime("%Y-%m-%d"),  # type: ignore
                query.end_date.strftime("%Y-%m-%d"),  # type: ignore
                query.frequency,
                query.transform,
                query.use_cache,
            )

        token = credentials.get("econdb_api_key", "")  # type: ignore
        # Attempt to create a temporary token if one is not supplied.
        if not token:
            token = await helpers.create_token(use_cache=query.use_cache)
            credentials.update({"econdb_api_key": token})  # type: ignore
        base_url = "https://www.econdb.com/api/series/?ticker="
        data: list[dict] = []
        symbols = query.symbol.split(",")
        countries = query.country.split(",") if query.country else []
        new_symbols: list = []
        # We need to join country, symbol, and transformation
        # for every combination of country and symbol.
        for s in symbols:
            # We will assume that if the symbol has a '~' in it,
            # the user knows what they are doing. We don't want to
            # match this defined symbol with any supplied country, and we need to
            # ignore the transform parameter because it has already been dictated by ~.
            # We will check if the transform is valid,
            # and return the symbol as 'level' if it is not.
            # We will also check if the symbol should have a country,
            # and if one was supplied.
            symbol = s.upper()
            if "~" in symbol:
                _symbol = symbol.split("~")[0]
                _transform = symbol.split("~")[1]
                if (
                    helpers.HAS_COUNTRIES.get(_symbol) is True
                    and _symbol in helpers.SYMBOL_TO_INDICATOR.values()
                ):
                    message = f"Invalid symbol: '{symbol}'. It must have a two-letter country code."
                    if len(symbols) > 1:
                        warn(message)
                        continue
                    raise OpenBBError(message)
                if _transform and _transform not in helpers.QUERY_TRANSFORMS:
                    message = f"Invalid transformation, '{_transform}', for symbol: '{_symbol}'."
                    if len(symbols) > 1:
                        warn(message)
                        new_symbols.append(_symbol)
                    else:
                        raise OpenBBError(message)
                elif not _transform:
                    new_symbols.append(symbol.replace("~", ""))
                else:
                    new_symbols.append(symbol)
            # Else we need to wrap each symbol with each country code
            # and check if the country is valid for that indicator.
            elif countries and helpers.HAS_COUNTRIES.get(symbol) is True:
                for country in countries:
                    _country = (
                        helpers.INDICATOR_COUNTRIES.get(symbol, [])
                        if country == "all"
                        else (
                            helpers.COUNTRY_GROUPS.get(country, [])
                            if country in helpers.COUNTRY_GROUPS
                            else (
                                [country.upper()]
                                if country.upper()
                                in helpers.INDICATOR_COUNTRIES.get(symbol, [])
                                else ""
                            )
                        )
                    )
                    if _country == "":
                        warn(
                            f"Invalid country code for indicator: {symbol}."
                            + f" Skipping '{country}'. Valid countries are:"
                            + f" {','.join(helpers.INDICATOR_COUNTRIES.get(symbol))}"
                        )
                        continue
                    new_symbol = [
                        symbol + d.upper()
                        for d in _country
                        if d in helpers.INDICATOR_COUNTRIES.get(symbol)
                    ]
                    if query.transform:
                        new_symbol = [
                            d + "~" + query.transform.upper() for d in new_symbol
                        ]
                    new_symbols.extend(new_symbol)
            # If it is a commodity symbol, there will be no country associated with the indicator.
            elif (
                symbol in helpers.HAS_COUNTRIES
                and helpers.HAS_COUNTRIES[symbol] is False
            ):
                new_symbols.append(symbol)
        if not new_symbols:
            symbol_message = helpers.INDICATOR_COUNTRIES.get(
                query.symbol.upper(), "None"
            )
            error_message = (
                "No valid combination of indicator symbols and countries were supplied."
                + f"\nValid countries for '{query.symbol}' are: {symbol_message}"
                + f"\nIf the symbol - {query.symbol} - is missing a country code."
                + " Please add the two-letter country code or use the country parameter."
                + "\nIf already included, add '~' to the end of the symbol."
            )
            raise OpenBBError(error_message)
        url = base_url + f"%5B{','.join(new_symbols)}%5D&format=json&token={token}"
        if query.start_date:
            url += f"&from={query.start_date}"
        if query.end_date:
            url += f"&to={query.end_date}"
        # If too many indicators and countries are supplied the request url will be too long.
        # Instead of chunking we request the user reduce the number of indicators and countries.
        # This might be able to nudge higher, but it is a safe limit for all operating systems.
        if len(url) > 2000:
            raise OpenBBError(
                "The request has generated a url that is too long."
                + " Please reduce the number of symbols or countries and try again."
            )

        async def response_callback(response, session):
            """Response callback."""
            if response.status != 200:
                warn(f"Error: {response.status} - {response.reason}")
            response = await response.json()
            if response.get("results"):
                data.extend(response["results"])
            while response.get("next"):
                response = await session.get(response["next"])
                response = await response.json()
                if response.get("results"):
                    data.extend(response["results"])
            return data

        if query.use_cache is True:
            cache_dir = f"{helpers.get_user_cache_directory()}/http/econdb_indicators"
            async with helpers.CachedSession(
                cache=helpers.SQLiteBackend(
                    cache_dir, expire_after=3600 * 24, ignored_params=["token"]
                )
            ) as session:
                try:
                    data = await helpers.amake_request(  # type: ignore
                        url,
                        session=session,
                        response_callback=response_callback,
                        timeout=20,
                        **kwargs,
                    )
                finally:
                    await session.close()
        else:
            data = await helpers.amake_request(  # type: ignore
                url, response_callback=response_callback, timeout=20, **kwargs
            )
        if not data:
            raise EmptyDataError()
        return data