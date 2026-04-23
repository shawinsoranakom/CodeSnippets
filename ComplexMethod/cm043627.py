async def aextract_data(
        query: FredSearchQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Extract the raw data."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from openbb_core.provider.utils.helpers import (
            amake_request,
            get_querystring,
        )

        api_key = credentials.get("fred_api_key") if credentials else ""

        if query.series_id is not None:
            results: list = []

            async def get_one(_id: str):
                """Get data for one series."""
                data: dict = {}
                url = f"https://api.stlouisfed.org/geofred/series/group?series_id={_id}&api_key={api_key}&file_type=json"
                response = await amake_request(url)
                data = response.get("series_group")  # type: ignore
                if data:
                    data.update({"series_id": _id})
                    results.append(data)

            await asyncio.gather(*[get_one(_id) for _id in query.series_id.split(",")])

            if results:
                return results
            raise EmptyDataError("No results found for the provided series_id(s).")

        if query.search_type == "release" and query.release_id is None:
            url = f"https://api.stlouisfed.org/fred/releases?api_key={api_key}&file_type=json"
            response = await amake_request(url)
            results = response.get("releases")  # type: ignore
            if results:
                return results
            raise OpenBBError(
                "Unexpected result while retrieving the list of releases from the FRED API."
            )

        url = (
            "https://api.stlouisfed.org/fred/release/series?"
            if query.release_id is not None
            else "https://api.stlouisfed.org/fred/series/search?"
        )

        exclude = (
            ["search_text", "limit"] if query.release_id is not None else ["limit"]
        )

        if query.release_id is not None and query.order_by == "search_rank":
            query.order_by = None  # type: ignore

        querystring = get_querystring(query.model_dump(), exclude).replace(" ", "%20")
        url = url + querystring + f"&file_type=json&api_key={api_key}"
        response = await amake_request(url)

        if isinstance(response, dict) and "error_code" in response:
            raise OpenBBError(
                f"FRED API Error -> Status Code: {response['error_code']} -> {response.get('error_message', '')}"
            )

        if isinstance(response, dict) and "count" in response:
            results = response.get("seriess", [])
            return results
        raise OpenBBError(
            f"Unexpected response format. Expected a dictionary, got {type(response)}"
        )