def straddle(
        self,
        days: int | None = None,
        strike: float | None = None,
        underlying_price: float | None = None,
    ) -> "DataFrame":
        """
        Calculate the cost of a straddle by DTE. Use a negative strike price for short options.

        Parameters
        ----------
        days: Optional[int]
            The target number of days until expiry. Default is 30 days.
        strike: Optional[float]
            The target strike price. Enter a negative value for short options.
            Default is the last price of the underlying stock.
        underlying_price: Optional[float]
            Only supply this is if the underlying price is not a returned field.

        Returns
        -------
        DataFrame
            Pandas DataFrame with the results.
                Strike 1 is the nearest call strike,
                Strike 2 is the nearest put strike.
        """
        # pylint: disable=import-outside-toplevel
        from numpy import inf
        from pandas import Series

        short: bool = False

        chains = self.dataframe

        if days is None:
            days = 30

        if days == 0:
            days = -1

        dte_estimate = self._get_nearest_expiration(days)

        chains = chains[chains.expiration.astype(str) == dte_estimate]

        if not hasattr(chains, "underlying_price") and underlying_price is None:
            raise OpenBBError(
                "Error: underlying_price must be provided if underlying_price is not available"
            )
        underlying_price = (
            underlying_price
            if underlying_price is not None
            else chains.underlying_price.iloc[0]
        )

        force_otm = True

        if strike is None and not hasattr(chains, "underlying_price"):
            raise OpenBBError(
                "Error: strike must be provided if underlying_price is not available"
            )

        if strike is not None:
            force_otm = False

        if strike is None:
            strike = underlying_price

        if strike is not None and strike < 0:
            short = True

        strike_price = abs(strike)  # type: ignore
        bid_ask = "bid" if short else "ask"
        call_price_col = self._identify_price_col(chains, "call", bid_ask)  # type: ignore
        put_price_col = self._identify_price_col(chains, "put", bid_ask)  # type: ignore
        call_strike_estimate = self._get_nearest_strike("call", days, strike_price, call_price_col, force_otm)  # type: ignore
        # If a strike price is supplied, the put strike is the same as the call strike.
        # Otherwise, the put strike is the nearest OTM put strike to the last price.

        put_strike_estimate = self._get_nearest_strike("put", days, strike_price, put_price_col, force_otm)  # type: ignore
        call_premium = chains[chains.strike == call_strike_estimate].query("`option_type` == 'call'")[  # type: ignore
            call_price_col
        ]
        put_premium = chains[chains.strike == put_strike_estimate].query("`option_type` == 'put'")[  # type: ignore
            put_price_col
        ]
        if call_premium.empty or put_premium.empty:
            raise OpenBBError(
                "Error: No premium data found for the selected strikes."
                f" Call: {call_strike_estimate}, Put: {put_strike_estimate}"
            )
        put_premium = put_premium.values[0]
        call_premium = call_premium.values[0]
        dte = chains[chains.expiration.astype(str) == dte_estimate]["dte"].unique()[0]  # type: ignore
        straddle_cost = call_premium + put_premium  # type: ignore
        straddle_dict: dict = {}

        # Includes the as-of date if it is historical EOD data.
        if hasattr(chains, "eod_date"):
            straddle_dict.update({"Date": chains.eod_date.iloc[0]})

        straddle_dict.update(
            {
                "Symbol": chains.underlying_symbol.unique()[0],
                "Underlying Price": underlying_price,
                "Expiration": dte_estimate,
                "DTE": dte,
                "Strike 1": call_strike_estimate,
                "Strike 2": put_strike_estimate,
                "Strike 1 Premium": call_premium,
                "Strike 2 Premium": put_premium,
                "Cost": straddle_cost * -1 if short else straddle_cost,
                "Cost Percent": round(
                    straddle_cost / underlying_price * 100, ndigits=4
                ),
                "Breakeven Upper": call_strike_estimate + straddle_cost,
                "Breakeven Upper Percent": round(
                    ((call_strike_estimate + straddle_cost) / underlying_price * 100)
                    - 100,
                    ndigits=4,
                ),
                "Breakeven Lower": put_strike_estimate - straddle_cost,
                "Breakeven Lower Percent": round(
                    -100
                    + (put_strike_estimate - straddle_cost) / underlying_price * 100,
                    ndigits=4,
                ),
                "Max Profit": abs(straddle_cost) if short else inf,
                "Max Loss": inf if short else straddle_cost * -1,
            }
        )
        straddle = Series(
            data=straddle_dict.values(),
            index=list(straddle_dict),  # type: ignore
        )
        straddle.name = "Short Straddle" if short else "Long Straddle"
        straddle.loc["Payoff Ratio"] = round(
            abs(straddle.loc["Max Profit"] / straddle.loc["Max Loss"]), ndigits=4
        )

        return straddle.to_frame()