def strangle(
        self,
        days: int | None = None,
        moneyness: float | None = None,
        underlying_price: float | None = None,
    ) -> "DataFrame":
        """
        Calculate the cost of a strangle by DTE and % moneyness. Use a negative value for moneyness for short options.

        Parameters
        ----------
        days: int
            The target number of days until expiry.  Default is 30 days.
        moneyness: float
            The percentage of OTM moneyness, expressed as a percent between -100 < 0 < 100.
            Enter a negative number for short options. Default is 5%.
        underlying_price: Optional[float]
            Only supply this is if the underlying price is not a returned field.

        Returns
        -------
        DataFrame
            Pandas DataFrame with the results.
                Strike 1 is the nearest call strike.
                Strike 2 is the nearest put strike.
        """
        # pylint: disable=import-outside-toplevel
        from numpy import inf
        from pandas import Series

        if days is None:
            days = 30

        if moneyness is None:
            moneyness = 5

        short: bool = False

        if moneyness < 0:
            short = True
        moneyness = abs(moneyness)

        bid_ask = "bid" if short else "ask"

        chains = self.dataframe
        dte_estimate = self._get_nearest_expiration(days)
        chains = chains[chains["expiration"].astype(str) == dte_estimate]
        call_price_col = self._identify_price_col(chains, "call", bid_ask)  # type: ignore
        put_price_col = self._identify_price_col(chains, "put", bid_ask)  # type: ignore

        if underlying_price is None and not hasattr(chains, "underlying_price"):
            raise OpenBBError(
                "Error: underlying_price must be provided if underlying_price is not available"
            )

        underlying_price = (
            underlying_price
            if underlying_price is not None
            else chains.underlying_price.iloc[0]
        )

        strikes = self._get_nearest_otm_strikes(
            dte_estimate, underlying_price, moneyness
        )
        call_strike_estimate = self._get_nearest_strike(
            "call", days, strikes.get("call"), call_price_col, force_otm=False
        )
        put_strike_estimate = self._get_nearest_strike(
            "put", days, strikes.get("put"), put_price_col, force_otm=False
        )
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
        strangle_cost = call_premium + put_premium
        underlying_price = (
            underlying_price
            if underlying_price is not None
            else chains.underlying_price.iloc[0]
        )
        strangle_dict: dict = {}
        # Includes the as-of date if it is historical EOD data.
        if hasattr(chains, "eod_date"):
            strangle_dict.update({"Date": chains.eod_date.iloc[0]})

        strangle_dict.update(
            {
                "Symbol": chains.underlying_symbol.unique()[0],
                "Underlying Price": underlying_price,
                "Expiration": dte_estimate,
                "DTE": dte,
                "Strike 1": call_strike_estimate,
                "Strike 2": put_strike_estimate,
                "Strike 1 Premium": call_premium,
                "Strike 2 Premium": put_premium,
                "Cost": strangle_cost * -1 if short else strangle_cost,
                "Cost Percent": round(
                    strangle_cost / underlying_price * 100, ndigits=4
                ),
                "Breakeven Upper": call_strike_estimate + strangle_cost,
                "Breakeven Upper Percent": round(
                    ((call_strike_estimate + strangle_cost) / underlying_price * 100)
                    - 100,
                    ndigits=4,
                ),
                "Breakeven Lower": put_strike_estimate - strangle_cost,
                "Breakeven Lower Percent": round(
                    (
                        -100
                        + (put_strike_estimate - strangle_cost) / underlying_price * 100
                    ),
                    ndigits=4,
                ),
                "Max Profit": abs(strangle_cost) if short else inf,
                "Max Loss": inf if short else strangle_cost * -1,
            }
        )
        strangle = Series(
            data=strangle_dict.values(),
            index=list(strangle_dict),  # type: ignore
        )
        strangle.name = "Short Strangle" if short else "Long Strangle"
        strangle.loc["Payoff Ratio"] = round(
            abs(strangle.loc["Max Profit"] / strangle.loc["Max Loss"]), ndigits=4
        )

        return strangle.to_frame()