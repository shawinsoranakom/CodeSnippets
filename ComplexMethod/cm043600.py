async def get_treasury_holdings(  # pylint: disable=R0917
        self,
        as_of: str | None = None,
        cusip: str | None = None,
        holding_type: str | None = None,
        wam: bool | None = False,
        monthly: bool | None = False,
    ) -> list[dict]:
        """Get the latest Treasury holdings, or as of a single date.

        Parameters
        ----------
        as_of: Optional[str]
            The as-of date to get data for. Defaults to the latest.
        cusip: Optional[str]
            The CUSIP of the security to search for. This parameter takes priority over `monthly` and `holding_type`.
        holding_type: Optional[str]
            The holding type for which to retrieve. Choices are: ['all', 'bills', 'notesbonds', 'frn', 'tips']
        wam: Optional[bool]
            Whether to return a single date weighted average maturity for Agency debt. Defaults to False.
            This parameter takes priority over `holding_type`, `cusip`, and `monthly`.
        monthly: Optional[bool]
            If true, returns historical data for all securities at a monthly interval.
            This parameter takes priority over other parameters except `wam`.

        Returns
        -------
        List[Dict]: List of dictionaries with results.

        Examples
        --------
        >>> holdings = await SomaHoldings().get_treasury_holdings(holding_type = "tips")

        >>> df = await SomaHoldings().get_treasury_holdings(cusip = "912810FH6")

        >>> wam = await SomaHoldings().get_treasury_holdings(wam = True)

        >>> monthly = await SomaHoldings().get_treasury_holdings(monthly = True, holding_type = "bills")
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
            ]["get_treasury_debts"]
            response = await fetch_data(url)
            return [response.get("soma", {})]

        if holding_type is not None:
            if holding_type not in TREASURY_HOLDING_TYPES:
                raise OpenBBError(
                    f"Invalid choice. Choose from: {', '.join(TREASURY_HOLDING_TYPES)}"
                )
            url = _get_endpoints(treasury_holding_type=holding_type, date=as_of)[
                "soma_holdings"
            ]["get_treasury_holding_type"]
        if monthly:
            url = _get_endpoints()["soma_holdings"]["get_treasury_monthly"]
        if cusip is not None:
            url = _get_endpoints(cusips=cusip)["soma_holdings"]["get_treasury_cusip"]

        response = await fetch_data(url)
        holdings = response.get("soma", {}).get("holdings", [])
        if not holdings:
            raise EmptyDataError()

        return holdings