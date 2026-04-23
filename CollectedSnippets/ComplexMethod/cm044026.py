def extract_data(
        query: NasdaqCompanyFilingsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Extract data from the query."""
        # pylint: disable=import-outside-toplevel
        import time  # noqa
        from openbb_core.provider.utils.errors import OpenBBError
        from openbb_core.provider.utils.helpers import get_requests_session
        from openbb_nasdaq.utils.helpers import get_headers
        from requests.exceptions import ReadTimeout
        from urllib3.exceptions import ReadTimeoutError

        if not query.symbol:
            raise OpenBBError("Symbol field is required.")

        base_url = f"https://api.nasdaq.com/api/company/{query.symbol}/sec-filings?"
        base_url += f"Year={query.year or datetime.now().year}&"
        form_group = form_groups.get(query.form_group)
        url_end = "&sortColumn=filed&sortOrder=desc&IsQuoteMedia=true"
        url = base_url + f"limit=100&FormGroup={form_group}" + url_end
        headers = get_headers(accept_type="json")
        del headers["Connection"]
        rows: list = []

        with get_requests_session() as session:
            try:
                response = session.get(url=url, headers=headers, timeout=10)
            except (ReadTimeout, ReadTimeoutError):
                time.sleep(2)
                try:
                    response = session.get(url=url, headers=headers, timeout=10)
                except (ReadTimeout, ReadTimeoutError) as e:
                    raise OpenBBError(e) from e

            if response.status_code != 200:
                raise OpenBBError(
                    f"Error fetching data from Nasdaq: {response.status_code} - {response.reason}"
                )
            data = response.json().get("data", {})
            rows = data.get("rows", [])
            total_records = (
                int(data.get("totalRecords")) if data.get("totalRecords") else 0
            )
            if total_records < 1:
                raise OpenBBError(
                    f"No data found for {query.symbol} in {query.year}, for form group, {form_group}."
                )
            n_rows = len(rows)
            while n_rows < total_records:
                offset = n_rows
                next_url = url + f"&offset={offset}"
                response = session.get(url=next_url, headers=headers, timeout=10)
                if response.status_code != 200:
                    raise OpenBBError(
                        f"Error fetching data from Nasdaq: {response.status_code} - {response.reason}"
                    )
                next_data = response.json().get("data", {})
                new_rows = next_data.get("rows", [])
                if not new_rows:
                    break
                rows.extend(new_rows)
                n_rows = len(rows)

            data["rows"] = rows
            if not data or not data.get("rows"):
                raise OpenBBError(
                    "No reports for the given symbol, year, and form group."
                )

            return data