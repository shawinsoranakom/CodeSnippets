async def aextract_data(
        query: BenzingaAnalystSearchQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Extract the raw data."""
        # pylint: disable=import-outside-toplevel
        from openbb_benzinga.utils.helpers import response_callback
        from openbb_core.provider.utils.helpers import amake_request, get_querystring

        token = credentials.get("benzinga_api_key") if credentials else ""
        querystring = get_querystring(query.model_dump(by_alias=True), [])
        url = f"https://api.benzinga.com/api/v2.1/calendar/ratings/analysts?{querystring}&token={token}"
        data = await amake_request(url, response_callback=response_callback, **kwargs)

        if (isinstance(data, list) and not data) or (
            isinstance(data, dict) and not data.get("analyst_ratings_analyst")
        ):
            raise EmptyDataError("No ratings data returned.")

        if isinstance(data, dict) and "analyst_ratings_analyst" not in data:
            raise OpenBBError(
                f"Unexpected data format. Expected 'analyst_ratings_analyst' key, got: {list(data.keys())}"
            )

        if not isinstance(data, dict):
            raise OpenBBError(
                f"Unexpected data format. Expected dict, got: {type(data).__name__}"
            )

        return data["analyst_ratings_analyst"]