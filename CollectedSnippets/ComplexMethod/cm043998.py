async def aextract_data(  # pylint: disable=R0914.R0912,R0915
        query: EconDbYieldCurveQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Extract the data."""
        # pylint: disable=import-outside-toplevel
        import asyncio  #  noqa
        from openbb_econdb.utils import helpers
        from warnings import warn

        token = credentials.get("econdb_api_key") if credentials else ""  # type: ignore
        # Attempt to create a temporary token if one is not supplied.
        if not token:
            token = await helpers.create_token(use_cache=query.use_cache)
            credentials.update({"econdb_api_key": token})  # type: ignore

        results: dict = {}
        messages: list = []

        async def get_one_country(country):
            """Get the data for one country."""
            base_url = "https://www.econdb.com/api/series/?ticker="
            symbols = list(COUNTRIES_DICT[country].keys())
            url = (
                base_url
                + f"%5B{','.join(symbols)}%5D&page_size=50&format=json&token={token}"
            )
            data: list = []
            response: dict | list[dict] = {}
            if query.use_cache is True:
                cache_dir = (
                    f"{helpers.get_user_cache_directory()}/http/econdb_yield_curve"
                )
                async with helpers.CachedSession(
                    cache=helpers.SQLiteBackend(
                        cache_dir, expire_after=3600 * 4, ignored_params=["token"]
                    )
                ) as session:
                    await session.delete_expired_responses()
                    try:
                        response = await helpers.amake_request(  # type: ignore
                            url,
                            session=session,
                            timeout=20,
                            **kwargs,
                        )
                    finally:
                        await session.close()
            else:
                response = await helpers.amake_request(url, timeout=20, **kwargs)  # type: ignore
            if not response:
                messages.append(f"No data was returned for, {country}")
                return
            data = response.get("results")  # type: ignore
            if not data:
                messages.append(f"The response for, {country}, was returned empty.")
                return
            results[country] = data

            return

        _countries = query.country.split(",")

        tasks = [asyncio.create_task(get_one_country(c)) for c in _countries]
        await asyncio.gather(*tasks)

        if not results and messages:
            msg_str = "\n".join(messages)
            raise OpenBBError(msg_str)

        if not results and not messages:
            raise OpenBBError("Unexpected outcome -> All requests were returned empty.")

        if results and messages:
            for message in messages:
                warn(message)

        return results