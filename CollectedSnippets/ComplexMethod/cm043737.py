def transform_data(
        query: SecCompanyFilingsQueryParams, data: list[dict], **kwargs: Any
    ) -> list[SecCompanyFilingsData]:
        """Transform the data."""
        # pylint: disable=import-outside-toplevel
        from numpy import nan
        from pandas import NA, DataFrame, to_datetime

        if not data:
            raise EmptyDataError(
                f"No filings found for CIK {query.cik}, or symbol {query.symbol}"
            )
        cols = [
            "reportDate",
            "filingDate",
            "acceptanceDateTime",
            "act",
            "form",
            "items",
            "primaryDocDescription",
            "primaryDocument",
            "accessionNumber",
            "fileNumber",
            "filmNumber",
            "isInlineXBRL",
            "isXBRL",
            "size",
        ]
        filings = DataFrame(data, columns=cols).astype(str)
        filings["reportDate"] = to_datetime(filings["reportDate"]).dt.date
        filings["filingDate"] = to_datetime(filings["filingDate"]).dt.date
        filings = filings.sort_values(by=["filingDate", "reportDate"], ascending=False)
        if query.start_date:
            filings = filings[filings["filingDate"] >= query.start_date]
        if query.end_date:
            filings = filings[filings["filingDate"] <= query.end_date]
        base_url = f"https://www.sec.gov/Archives/edgar/data/{str(int(query.cik))}/"  # type: ignore
        filings["primaryDocumentUrl"] = (
            base_url
            + filings["accessionNumber"].str.replace("-", "")
            + "/"
            + filings["primaryDocument"]
        )
        filings["completeSubmissionUrl"] = (
            base_url + filings["accessionNumber"] + ".txt"
        )
        filings["filingDetailUrl"] = (
            base_url + filings["accessionNumber"] + "-index.htm"
        )
        if query.form_type:
            form_types = query.form_type.replace("_", " ").split(",")
            filings = filings[
                filings.form.str.contains("|".join(form_types), case=False, na=False)
            ]
        if query.limit:
            filings = filings.head(query.limit) if query.limit != 0 else filings

        if len(filings) == 0:
            raise EmptyDataError("No filings were found using the filters provided.")
        filings = filings.replace({NA: None, nan: None})

        return [
            SecCompanyFilingsData.model_validate(d) for d in filings.to_dict("records")
        ]