async def get_agency_holdings(
        self,
        as_of: str | None = None,
        cusip: str | None = None,
        holding_type: str | None = None,
        wam: bool = False,
    ) -> list[dict]:
        """Get the latest agency holdings, or as of a single date. Data is updated weekly.

        Parameters
        ----------
        as_of: Optional[str]
            The as-of date to get data for. Defaults to the latest.
        cusip: Optional[str]
            The CUSIP of the security to search for. This parameter takes priority over `holding_type`.
        holding_type: Optional[str]
            The holding type for which to retrieve. Choices are: ['all', 'agency debts', 'mbs', 'cmbs']
        wam: Optional[bool]
            Whether to return a single date weighted average maturity for Agency debt. Defaults to False.
            This parameter takes priority over `holding_type` and `cusip`.

        Returns
        -------
        List[Dict]: List of dictionaries with results.

        Examples
        --------
        >>> holdings = await SomaHoldings().get_agency_holdings(holding_type = "cmbs")

        >>> df = await SomaHoldings().get_agency_holdings(cusip = "3138LMCK7")

        >>> wam = await SomaHoldings().get_agency_holdings(wam = True)
        """
        response: dict = {}
        url: str = ""
        dates = await self.get_as_of_dates()
        if as_of is not None:
            as_of = get_nearest_date(dates, as_of)
        if as_of is None:
            as_of = dates[0]
        if wam is True:
            url = _get_endpoints(
                date=as_of,
            )[
                "soma_holdings"
            ]["agency_debts"]
            response = await fetch_data(url)
            return [response.get("soma", {})]
        url = _get_endpoints(date=as_of)["soma_holdings"]["get_as_of"]
        if holding_type is not None:
            if holding_type not in AGENCY_HOLDING_TYPES:
                raise OpenBBError(
                    "Invalid choice. Choose from: ['all', 'agency debts', 'mbs', 'cmbs']"
                )
            url = _get_endpoints(
                agency_holding_type=AGENCY_HOLDING_TYPES[holding_type], date=as_of
            )["soma_holdings"]["get_holding_type"]
        if cusip is not None:
            url = _get_endpoints(cusips=cusip)["soma_holdings"]["get_cusip"]
        response = await fetch_data(url)
        holdings = response.get("soma", {}).get("holdings", [])
        if not holdings:
            raise EmptyDataError()

        return holdings