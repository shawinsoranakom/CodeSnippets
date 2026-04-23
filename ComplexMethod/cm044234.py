def vertical_call_spread(
        self,
        days: int | None = None,
        sold: float | None = None,
        bought: float | None = None,
        underlying_price: float | None = None,
    ) -> "DataFrame":
        """
        Calculate the vertical call spread for the target DTE.
        A bull call spread is when the sold strike is above the bought strike.

        Parameters
        ----------
        days: int
            The target number of days until expiry. This value will be used to get the nearest valid DTE.
            Default is 30 days.
        sold: float
            The target strike price for the short leg of the vertical call spread.
            Default is 7.5% above the last price of the underlying.
        bought: float
            The target strike price for the long leg of the vertical call spread.
            Default is 2.5% above the last price of the underlying.
        underlying_price: Optional[float]
            Only supply this is if the underlying price is not a returned field.

        Returns
        -------
        DataFrame
            Pandas DataFrame with the results.
                Strike 1 is the sold call strike.
                Strike 2 is the bought call strike.
        """
        # pylint: disable=import-outside-toplevel
        from numpy import nan
        from pandas import DataFrame, Series

        chains = self.dataframe

        if not hasattr(chains, "underlying_price") and underlying_price is None:
            raise OpenBBError(
                "Error: underlying_price must be provided if underlying_price is not available"
            )

        if days is None:
            days = 30

        if days == 0:
            days = -1

        dte_estimate = self._get_nearest_expiration(days)

        chains = chains[chains["expiration"].astype(str) == dte_estimate].query(
            "`option_type` == 'call'"
        )

        last_price = (
            underlying_price
            if underlying_price is not None
            else chains.underlying_price.iloc[0]
        )

        if bought is None:
            bought = last_price * 1.0250

        if sold is None:
            sold = last_price * 1.0750

        bid = self._identify_price_col(chains, "call", "bid")
        ask = self._identify_price_col(chains, "call", "ask")
        sold = self._get_nearest_strike("call", days, sold, bid, False)
        bought = self._get_nearest_strike("call", days, bought, ask, False)

        sold_premium = chains[chains.strike == sold][bid].iloc[0] * (-1)  # type: ignore
        bought_premium = chains[chains.strike == bought][ask].iloc[0]  # type: ignore
        dte = chains[chains.expiration.astype(str) == dte_estimate]["dte"].unique()[0]  # type: ignore
        spread_cost = bought_premium + sold_premium
        breakeven_price = bought + spread_cost
        max_profit = sold - bought - spread_cost  # type: ignore
        call_spread_: dict = {}
        if sold != bought and spread_cost != 0:
            # Includes the as-of date if it is historical EOD data.
            if hasattr(chains, "eod_date"):
                call_spread_.update({"Date": chains.eod_date.iloc[0]})

            call_spread_.update(
                {
                    "Symbol": chains.underlying_symbol.unique()[0],
                    "Underlying Price": last_price,
                    "Expiration": dte_estimate,
                    "DTE": dte,
                    "Strike 1": sold,
                    "Strike 2": bought,
                    "Strike 1 Premium": sold_premium,
                    "Strike 2 Premium": bought_premium,
                    "Cost": spread_cost,
                    "Cost Percent": round(spread_cost / last_price * 100, ndigits=4),
                    "Breakeven Lower": breakeven_price,
                    "Breakeven Lower Percent": round(
                        (breakeven_price / last_price * 100) - 100, ndigits=4
                    ),
                    "Breakeven Upper": nan,
                    "Breakeven Upper Percent": nan,
                    "Max Profit": max_profit,
                    "Max Loss": spread_cost * -1,
                }
            )
            call_spread = Series(
                data=call_spread_.values(),
                index=list(call_spread_),  # type: ignore
            )
            call_spread.name = "Bull Call Spread"

            if call_spread.loc["Cost"] < 0:
                call_spread.loc["Max Profit"] = call_spread.loc["Cost"] * -1
                call_spread.loc["Max Loss"] = -1 * (bought - sold + call_spread.loc["Cost"])  # type: ignore
                lower = bought if sold > bought else sold  # type: ignore
                call_spread.loc["Breakeven Upper"] = (
                    lower + call_spread.loc["Max Profit"]
                )
                call_spread.loc["Breakeven Upper Percent"] = round(
                    (breakeven_price / last_price * 100) - 100, ndigits=4
                )
                call_spread.loc["Breakeven Lower"] = nan
                call_spread.loc["Breakeven Lower Percent"] = nan
                call_spread.name = "Bear Call Spread"

            call_spread.loc["Payoff Ratio"] = round(
                abs(call_spread.loc["Max Profit"] / call_spread.loc["Max Loss"]),
                ndigits=4,
            )

            return call_spread.to_frame()

        return DataFrame()