async def aextract_data(
        query: CongressBillInfoQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Extract data from the query."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.model.abstract.error import OpenBBError
        from openbb_core.provider.utils.errors import UnauthorizedError
        from openbb_core.provider.utils.helpers import amake_request

        api_key = credentials.get("congress_gov_api_key", "") if credentials else ""
        bill_url = query.bill_url
        if bill_url[0].isnumeric() or (bill_url[0] == "/" and bill_url[1].isnumeric()):
            # If the bill URL starts with a number, assume it's a congress number and construct the URL
            bill_url = (
                "https://api.congress.gov/v3/bill/"
                + f"{bill_url[1:] if bill_url[0] == '/' else bill_url}?format=json"
            )

        url = bill_url + "&api_key=" + api_key
        base_info: dict = await amake_request(url)  # type: ignore

        if isinstance(base_info, dict) and (error := base_info.get("error", {})):
            if "API_KEY" in error.get("code", ""):
                raise UnauthorizedError(
                    f"{error.get('code', '')} -> {error.get('message', '')}"
                )
            raise OpenBBError(f"{error.get('code', '')} -> {error.get('message', '')}")

        base_info = base_info.get("bill", {})
        cosponsors = base_info.get("cosponsors", {})

        if cosponsors.get("count", 0) > 0:
            cosponsors_url = (
                base_info.get("cosponsors", {}).get("url", "") + "&api_key=" + api_key
            )
            cosponsors_response: dict = await amake_request(cosponsors_url)  # type: ignore
            cosponsors_list = cosponsors_response.get("cosponsors", [])
            base_info["cosponsors"] = cosponsors_list

        subjects = base_info.get("subjects", {})

        if subjects.get("count", 0) > 0:
            subjects_url = (
                base_info.get("subjects", {}).get("url", "") + "&api_key=" + api_key
            )
            subjects_response: dict = await amake_request(subjects_url)  # type: ignore
            subjects_list = subjects_response.get("subjects", {}).get(
                "legislativeSubjects", []
            )
            base_info["subjects"] = subjects_list

        summaries = base_info.get("summaries", {})

        if summaries.get("count", 0) > 0:
            summaries_url = (
                base_info.get("summaries", {}).get("url", "") + "&api_key=" + api_key
            )
            summaries_response: dict = await amake_request(summaries_url)  # type: ignore
            summaries_list = summaries_response.get("summaries", [])

            if summaries_list:
                base_info["summaries"] = summaries_list

        committees = base_info.get("committees", {})

        if committees.get("count", 0) > 0:
            committees_url = (
                base_info.get("committees", {}).get("url", "") + "&api_key=" + api_key
            )
            committees_response: dict = await amake_request(committees_url)  # type: ignore
            committees_list = committees_response.get("committees", [])

            if committees_list:
                base_info["committees"] = committees_list

        actions = base_info.get("actions", {})

        if actions.get("count", 0) > 0:
            actions_url = (
                base_info.get("actions", {}).get("url", "") + "&api_key=" + api_key
            )
            actions_response: dict = await amake_request(actions_url)  # type: ignore
            actions_list = actions_response.get("actions", [])

            if actions_list:
                base_info["actions"] = actions_list

        titles = base_info.get("titles", {})

        if titles.get("count", 0) > 0:
            titles_url = (
                base_info.get("titles", {}).get("url", "") + "&api_key=" + api_key
            )
            titles_response: dict = await amake_request(titles_url)  # type: ignore
            titles_list = titles_response.get("titles", [])

            if titles_list:
                base_info["titles"] = titles_list

        related_bills = base_info.get("relatedBills", {})

        if related_bills.get("count", 0) > 0:
            related_bills_url = (
                base_info.get("relatedBills", {}).get("url", "") + "&api_key=" + api_key
            )
            related_bills_response: dict = await amake_request(related_bills_url)  # type: ignore
            related_bills_list = related_bills_response.get("relatedBills", [])

            if related_bills_list:
                base_info["relatedBills"] = related_bills_list

        return base_info