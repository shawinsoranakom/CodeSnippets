async def aextract_data(
        query: CongressAmendmentsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list:
        """Extract data from the Congress API."""
        # pylint: disable=import-outside-toplevel
        import asyncio

        from openbb_congress_gov.utils.helpers import get_all_amendments_by_type
        from openbb_core.provider.utils.errors import UnauthorizedError
        from openbb_core.provider.utils.helpers import amake_request

        api_key = credentials.get("congress_gov_api_key") if credentials else ""

        if query.limit == 0 and query.amendment_type is not None:
            if query.congress is None:
                raise OpenBBError(
                    ValueError("'congress' is required when 'limit' is set to 0.")
                )

            return await get_all_amendments_by_type(
                congress=query.congress,
                amendment_type=query.amendment_type,
            )

        url = f"{base_url}amendment"

        if query.congress is not None:
            url += f"/{query.congress}"

            if query.amendment_type is not None:
                url += f"/{query.amendment_type}"

        url += f"?limit={query.limit if query.limit is not None else 100}"
        url += f"&offset={query.offset if query.offset else 0}"
        url += f"&sort=updateDate+{query.sort_by}"

        if query.start_date:
            url += f"&fromDateTime={query.start_date}T00:00:00Z"

        if query.end_date:
            url += f"&toDateTime={query.end_date}T23:59:59Z"

        url += f"&format=json&api_key={api_key}"

        try:
            response = await amake_request(url=url)

            if isinstance(response, dict) and (error := response.get("error", {})):
                if "API_KEY" in error.get("code", ""):
                    raise UnauthorizedError(
                        f"{error.get('code', '')} -> {error.get('message', '')}"
                    )
                raise OpenBBError(  # noqa: TRY301
                    f"{error.get('code', '')} -> {error.get('message', '')}"
                )
        except OpenBBError:
            raise
        except Exception as e:
            raise OpenBBError(e) from e

        amendments = response.get("amendments", [])  # type: ignore

        if not amendments:
            return []

        detail_urls = [
            a["url"].split("?")[0] + f"?format=json&api_key={api_key}"
            for a in amendments
            if "url" in a
        ]
        detail_responses = await asyncio.gather(
            *[amake_request(u) for u in detail_urls],
            return_exceptions=True,
        )

        for amendment, detail_resp in zip(amendments, detail_responses):
            if not isinstance(detail_resp, dict):
                continue

            detail = detail_resp.get("amendment", {})

            for field in (
                "amendedBill",
                "amendedAmendment",
                "sponsors",
                "submittedDate",
                "purpose",
            ):
                if field in detail and field not in amendment:
                    amendment[field] = detail[field]

            for field in ("latestAction", "description"):
                if field not in amendment and field in detail:
                    amendment[field] = detail[field]

        return amendments