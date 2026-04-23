async def aextract_data(
        query: CongressAmendmentInfoQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Extract data from the Congress API."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.model.abstract.error import OpenBBError
        from openbb_core.provider.utils.errors import UnauthorizedError
        from openbb_core.provider.utils.helpers import amake_request

        api_key = credentials.get("congress_gov_api_key", "") if credentials else ""
        amendment_url = query.amendment_url

        if amendment_url[0].isnumeric() or (
            amendment_url[0] == "/" and amendment_url[1].isnumeric()
        ):
            amendment_url = (
                "https://api.congress.gov/v3/amendment/"
                + f"{amendment_url[1:] if amendment_url[0] == '/' else amendment_url}?format=json"
            )

        url = amendment_url + "&api_key=" + api_key
        base_info: dict = await amake_request(url)  # type: ignore

        if isinstance(base_info, dict) and (error := base_info.get("error", {})):
            if "API_KEY" in error.get("code", ""):
                raise UnauthorizedError(
                    f"{error.get('code', '')} -> {error.get('message', '')}"
                )
            raise OpenBBError(f"{error.get('code', '')} -> {error.get('message', '')}")

        base_info = base_info.get("amendment", {})

        cosponsors = base_info.get("cosponsors", {})
        if isinstance(cosponsors, dict) and cosponsors.get("count", 0) > 0:
            cosponsors_url = cosponsors.get("url", "") + "&api_key=" + api_key
            cosponsors_response: dict = await amake_request(cosponsors_url)  # type: ignore
            cosponsors_list = cosponsors_response.get("cosponsors", [])
            if cosponsors_list:
                base_info["cosponsors"] = cosponsors_list

        actions = base_info.get("actions", {})
        if actions.get("count", 0) > 0:
            actions_url = actions.get("url", "") + "&api_key=" + api_key
            actions_response: dict = await amake_request(actions_url)  # type: ignore
            actions_list = actions_response.get("actions", [])
            if actions_list:
                base_info["actions"] = actions_list

        text_versions = base_info.get("textVersions", {})
        if isinstance(text_versions, dict) and text_versions.get("count", 0) > 0:
            text_url = text_versions.get("url", "") + "&api_key=" + api_key
            text_response: dict = await amake_request(text_url)  # type: ignore
            text_list = text_response.get("textVersions", [])
            if text_list:
                base_info["textVersions"] = text_list

        return base_info