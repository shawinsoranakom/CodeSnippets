def synthetic_long(
        self,
        days: int | None = 30,
        strike: float = 0,
        underlying_price: float | None = None,
    ) -> "DataFrame":
        """
        Calculate the cost of a synthetic long position at a given strike.
        It is expressed as the difference between a bought call and a sold put.

        Parameters
        -----------
        days: int
            The target number of days until expiry. Default is 30 days.
        strike: float
            The target strike price. Default is the last price of the underlying stock.
        underlying_price: Optional[float]
            Only supply this is if the underlying price is not a returned field.

        Returns
        -------
        DataFrame
            Pandas DataFrame with the results.
                Strike1 is the purchased call strike.
                Strike2 is the sold put strike.
        """
        # pylint: disable=import-outside-toplevel
        from numpy import inf, nan
        from pandas import DataFrame

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
        chains = DataFrame(chains[chains["expiration"].astype(str) == dte_estimate])
        last_price = (
            underlying_price
            if underlying_price is not None
            else chains.underlying_price.iloc[0]
        )
        bid = self._identify_price_col(chains, "put", "bid")
        ask = self._identify_price_col(chains, "call", "ask")
        strike_price = last_price if strike == 0 else strike
        sold = self._get_nearest_strike("put", days, strike_price, bid, False)
        bought = self._get_nearest_strike("call", days, strike_price, ask, False)
        put_premium = chains[chains.strike == sold].query("`option_type` == 'put'")[bid]  # type: ignore
        call_premium = chains[chains.strike == bought].query("`option_type` == 'call'")[ask]  # type: ignore

        if call_premium.empty or put_premium.empty:
            raise OpenBBError(
                f"Error: No premium data found for the selected strikes. Call: {bought}, Put: {sold}"
            )

        put_premium = put_premium.values[0] * (-1)
        call_premium = call_premium.values[0]
        dte = chains[chains.expiration.astype(str) == dte_estimate]["dte"].unique()[0]  # type: ignore
        position_cost = call_premium + put_premium
        breakeven = ((sold + bought) / 2) + position_cost  # type: ignore
        synthetic_long_dict: dict = {}
        # Includes the as-of date if it is historical EOD data.
        if hasattr(chains, "eod_date"):
            synthetic_long_dict.update({"Date": chains.eod_date.iloc[0]})

        synthetic_long_dict.update(
            {
                "Symbol": chains.underlying_symbol.unique()[0],
                "Underlying Price": last_price,
                "Expiration": dte_estimate,
                "DTE": dte,
                "Strike 1": sold,
                "Strike 2": bought,
                "Strike 1 Premium": call_premium,
                "Strike 2 Premium": put_premium,
                "Cost": position_cost,
                "Cost Percent": round(position_cost / last_price * 100, ndigits=4),
                "Breakeven Lower": nan,
                "Breakeven Lower Percent": nan,
                "Breakeven Upper": breakeven,
                "Breakeven Upper Percent": round(
                    ((breakeven - last_price) / last_price) * 100, ndigits=4
                ),
                "Max Profit": inf,
                "Max Loss": breakeven * (-1),
            }
        )

        synthetic_long = DataFrame(
            data=synthetic_long_dict.values(),
            index=list(synthetic_long_dict),  # type: ignore
        ).rename(columns={0: "Synthetic Long"})

        return synthetic_long