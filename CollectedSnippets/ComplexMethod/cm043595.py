async def aextract_data(
        query: FederalReserveCentralBankHoldingsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the FederalReserve endpoint."""
        # pylint: disable=import-outside-toplevel
        from openbb_federal_reserve.utils.ny_fed_api import SomaHoldings

        hold_type = "all" if "all" in query.holding_type else query.holding_type
        security_type = query.holding_type
        date = query.date.strftime("%Y-%m-%d") if query.date else None
        if (
            query.holding_type == "all_agency"
            or query.holding_type in AGENCY_HOLDING_TYPES
        ):
            security_type = "agency"  # type: ignore
        if (
            query.holding_type == "all_treasury"
            or query.holding_type in TREASURY_HOLDING_TYPES
        ):
            security_type = "treasury"  # type: ignore
        if query.cusip is not None:
            cusips = (
                query.cusip if isinstance(query.cusip, str) else ",".join(query.cusip)
            )
            return (
                await SomaHoldings().get_agency_holdings(cusip=cusips, as_of=date)
                if security_type == "agency"
                else await SomaHoldings().get_treasury_holdings(
                    cusip=cusips, as_of=date
                )
            )
        if query.summary is True:
            return await SomaHoldings().get_summary()
        if query.monthly is True:
            return await SomaHoldings().get_treasury_holdings(
                monthly=True, holding_type=hold_type
            )
        if security_type == "treasury" and query.wam is True:
            return await SomaHoldings().get_treasury_holdings(wam=True, as_of=date)
        if security_type == "agency" and query.wam is True:
            return await SomaHoldings().get_agency_holdings(wam=True, as_of=date)
        return (
            await SomaHoldings().get_agency_holdings(as_of=date, holding_type=hold_type)
            if security_type == "agency"
            else await SomaHoldings().get_treasury_holdings(
                as_of=date, holding_type=hold_type
            )
        )