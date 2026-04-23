def vertical_put_spread(
        self,
        days: int | None = None,
        sold: float | None = None,
        bought: float | None = None,
        underlying_price: float | None = None,
    ) -> "DataFrame":
        """
        Calculate the vertical put spread for the target DTE.
        A bear put spread is when the bought strike is above the sold strike.

        Parameters
        ----------
        days: int
            The target number of days until expiry. This value will be used to get the nearest valid DTE.
            Default is 30 days.
        sold: float
            The target strike price for the short leg of the vertical put spread.
            Default is 7.5% below the last price of the underlying.
        bought: float
            The target strike price for the long leg of the vertical put spread.
            Default is 2.5% below the last price of the underlying.
        underlying_price: Optional[float]
            Only supply this is if the underlying price is not a returned field.

        Returns
        -------
        DataFrame
            Pandas DataFrame with the results.
                Strike 1 is the sold strike.
                Strike 2 is the bought strike.
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
            "`option_type` == 'put'"
        )

        last_price = (
            underlying_price
            if underlying_price is not None
            else chains.underlying_price.iloc[0]
        )

        if bought is None:
            bought = last_price * 0.9750

        if sold is None:
            sold = last_price * 0.9250

        bid = self._identify_price_col(chains, "put", "bid")
        ask = self._identify_price_col(chains, "put", "ask")
        sold = self._get_nearest_strike("put", days, sold, bid, False)
        bought = self._get_nearest_strike("put", days, bought, ask, False)

        sold_premium = chains[chains.strike == sold][bid].iloc[0] * (-1)  # type: ignore
        bought_premium = chains[chains.strike == bought][ask].iloc[0]  # type: ignore
        dte = chains[chains.expiration.astype(str) == dte_estimate]["dte"].unique()[0]  # type: ignore
        spread_cost = bought_premium + sold_premium
        max_profit = abs(spread_cost)
        breakeven_price = sold - max_profit
        max_loss = (sold - bought - max_profit) * -1  # type: ignore
        put_spread_: dict = {}
        if sold != bought and max_loss != 0:
            # Includes the as-of date if it is historical EOD data.
            if hasattr(chains, "eod_date"):
                put_spread_.update({"Date": chains.eod_date.iloc[0]})

            put_spread_.update(
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
                    "Cost Percent": round(max_profit / last_price * 100, ndigits=4),
                    "Breakeven Lower": nan,
                    "Breakeven Lower Percent": nan,
                    "Breakeven Upper": breakeven_price,
                    "Breakeven Upper Percent": (
                        100 - round((breakeven_price / last_price) * 100, ndigits=4)
                    ),
                    "Max Profit": max_profit,
                    "Max Loss": max_loss,
                }
            )

            put_spread = Series(data=put_spread_.values(), index=put_spread_)
            put_spread.name = "Bull Put Spread"
            if put_spread.loc["Cost"] > 0:
                put_spread.loc["Max Profit"] = bought - sold - spread_cost  # type: ignore
                put_spread.loc["Max Loss"] = spread_cost * (-1)
                put_spread.loc["Breakeven Lower"] = bought - spread_cost
                put_spread.loc["Breakeven Lower Percent"] = 100 - round(
                    (breakeven_price / last_price) * 100, ndigits=4
                )
                put_spread.loc["Breakeven Upper"] = nan
                put_spread.loc["Breakeven Upper Percent"] = nan
                put_spread.name = "Bear Put Spread"

            put_spread.loc["Payoff Ratio"] = round(
                abs(put_spread.loc["Max Profit"] / put_spread.loc["Max Loss"]),
                ndigits=4,
            )

            return put_spread.to_frame()

        return DataFrame()