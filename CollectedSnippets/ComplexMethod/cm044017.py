async def aextract_data(
        query: BenzingaPriceTargetQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the Benzinga endpoint."""
        # pylint: disable=import-outside-toplevel
        from openbb_benzinga.utils.helpers import response_callback
        from openbb_core.provider.utils.helpers import amake_request, get_querystring

        token = credentials.get("benzinga_api_key") if credentials else ""
        base_url = "https://api.benzinga.com/api/v2.1/calendar/ratings"
        query.limit = query.limit or 200
        querystring = get_querystring(query.model_dump(by_alias=True), [])

        url = f"{base_url}?{querystring}&token={token}"
        data = await amake_request(url, response_callback=response_callback, **kwargs)

        if isinstance(data, dict) and "ratings" not in data:
            raise OpenBBError(
                f"Unexpected data format. Expected 'ratings' key, got: {list(data.keys())}"
            )
        if not isinstance(data, dict):
            raise OpenBBError(
                f"Unexpected data format. Expected dict, got: {type(data)}"
            )
        if isinstance(data, dict) and not data.get("ratings"):
            raise EmptyDataError("No ratings data returned.")

        return data["ratings"]