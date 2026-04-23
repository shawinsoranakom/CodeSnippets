def skew(
        self,
        date: str | int | None = None,
        moneyness: float | None = None,
        underlying_price: float | None = None,
    ) -> "DataFrame":
        """Return skewness of the options, either vertical or horizontal.

        The vertical skew for each expiry and option is calculated by subtracting the IV of the ATM call or put.
        Returns only where the IV is greater than 0.

        Horizontal skew is returned if a value for moneyness is supplied.
        It is expressed as the difference between skews of two equidistant OTM strikes (the closest call and put).

        Default state is 20% moneyness with 30 days until expiry.

        Parameters
        -----------
        date: Optional[Union[str, int]]
            The expiration date, or days until expiry, to use. Enter -1 for all expirations.
            Large chains (SPY, SPX, etc.) may take a few seconds to process when using -1.
        moneyness: float
            The moneyness to target for calculating horizontal skew.
        underlying_price: Optional[float]
            Only supply this is if the underlying price is not a returned field.

        Returns
        --------
        DataFrame
            Pandas DataFrame with the results.
        """
        # pylint: disable=import-outside-toplevel
        from pandas import DataFrame, concat

        data = self.dataframe
        expiration: str = ""
        if self.has_iv is False:
            raise OpenBBError("Error: 'implied_volatility' field not found.")

        data = DataFrame(data[data.implied_volatility > 0])  # type: ignore
        call_price_col = self._identify_price_col(data, "call", "ask")
        put_price_col = self._identify_price_col(data, "put", "ask")

        if not hasattr(data, "underlying_price") and underlying_price is None:
            raise OpenBBError(
                "Error: underlying_price must be provided if underlying_price is not available"
            )

        if moneyness is not None and date is None:
            date = -1

        if moneyness is None and date is None:
            date = 30
            moneyness = 20

        if date is None:
            date = 30  # type: ignore

        if date == -1:
            date = None

        if date is not None:
            if date not in self.expirations:
                expiration = self._get_nearest_expiration(date, df=data)
            data = data[data.expiration.astype(str) == expiration]

        days = data.dte.unique().tolist()  # type: ignore

        call_skew = DataFrame()
        put_skew = DataFrame()
        skew_df = DataFrame()
        puts = DataFrame()
        calls = DataFrame()

        # Horizontal skew
        if moneyness is not None:
            atm_call_iv = DataFrame()
            atm_put_iv = DataFrame()
            for day in days:
                strikes = self._get_nearest_otm_strikes(
                    date=day, moneyness=moneyness, underlying_price=underlying_price
                )
                atm_call_strike = self._get_nearest_strike(  # noqa:F841
                    "call", day, underlying_price, call_price_col, False
                )
                call_strike = self._get_nearest_strike(
                    "call", day, strikes["call"], call_price_col, False
                )  # noqa:F841
                _calls = data[data.dte == day].query("`option_type` == 'call'").copy()  # type: ignore
                last_price = (
                    underlying_price
                    if underlying_price is not None
                    else _calls.underlying_price.iloc[0]
                )
                if len(_calls) > 0:
                    call_iv = _calls[_calls.strike == call_strike][
                        ["expiration", "strike", "implied_volatility"]
                    ]
                    atm_call = _calls[_calls.strike == atm_call_strike][
                        ["expiration", "strike", "implied_volatility"]
                    ]
                    if len(atm_call) > 0:
                        calls = concat([calls, call_iv])  # type: ignore
                        atm_call_iv = concat([atm_call_iv, atm_call])  # type: ignore

                atm_put_strike = self._get_nearest_strike(
                    "put", day, last_price, put_price_col, False
                )  # noqa:F841
                put_strike = self._get_nearest_strike(
                    "put", day, strikes["put"], put_price_col, False
                )  # noqa:F841
                _puts = data[data.dte == day].query("`option_type` == 'put'").copy()  # type: ignore
                if len(_puts) > 0:
                    put_iv = _puts[_puts.strike == put_strike][
                        ["expiration", "strike", "implied_volatility"]
                    ]
                    atm_put = _puts[_puts.strike == atm_put_strike][
                        ["expiration", "strike", "implied_volatility"]
                    ]
                    if len(atm_put) > 0:  # type: ignore
                        puts = concat([puts, put_iv])  # type: ignore
                        atm_put_iv = concat([atm_put_iv, atm_put])  # type: ignore

            if calls.empty or puts.empty:
                raise OpenBBError(
                    "Error: Not enough information to complete the operation."
                    " Likely due to zero values in the IV field of the expiration."
                )

            calls = calls.drop_duplicates(subset=["expiration"]).set_index("expiration")  # type: ignore
            atm_call_iv = atm_call_iv.drop_duplicates(subset=["expiration"]).set_index("expiration")  # type: ignore
            puts = puts.drop_duplicates(subset=["expiration"]).set_index("expiration")  # type: ignore
            atm_put_iv = atm_put_iv.drop_duplicates(subset=["expiration"]).set_index("expiration")  # type: ignore
            skew_df["Call Strike"] = calls["strike"]
            skew_df["Call IV"] = calls["implied_volatility"]
            skew_df["Call ATM IV"] = atm_call_iv["implied_volatility"]
            skew_df["Call Skew"] = skew_df["Call IV"] - skew_df["Call ATM IV"]
            skew_df["Put Strike"] = puts["strike"]
            skew_df["Put IV"] = puts["implied_volatility"]
            skew_df["Put ATM IV"] = atm_put_iv["implied_volatility"]
            skew_df["Put Skew"] = skew_df["Put IV"] - skew_df["Put ATM IV"]
            skew_df["ATM Skew"] = skew_df["Call ATM IV"] - skew_df["Put ATM IV"]
            skew_df["IV Skew"] = skew_df["Call Skew"] - skew_df["Put Skew"]
            skew_df = skew_df.reset_index().rename(columns={"expiration": "Expiration"})
            skew_df["Expiration"] = skew_df["Expiration"].astype(str)

            return skew_df

        # Vertical skew

        calls = data[data.option_type == "call"]
        puts = data[data.option_type == "put"]

        for day in days:
            atm_call_strike = self._get_nearest_strike(
                "call", day, underlying_price, force_otm=False
            )  # noqa:F841
            _calls = calls[calls["dte"] == day][
                ["expiration", "option_type", "strike", "implied_volatility"]
            ]

            if len(_calls) > 0:
                call = _calls.set_index("expiration").copy()  # type: ignore
                call_atm_iv = call.query("`strike` == @atm_call_strike")[
                    "implied_volatility"
                ]
                if len(call_atm_iv) > 0:
                    call["ATM IV"] = call_atm_iv.iloc[0]
                    call["Skew"] = call["implied_volatility"] - call["ATM IV"]
                    call_skew = concat([call_skew, call])

            atm_put_strike = self._get_nearest_strike(
                "put", day, force_otm=False
            )  # noqa:F841
            _puts = puts[puts["dte"] == day][
                ["expiration", "option_type", "strike", "implied_volatility"]
            ]

            if len(_puts) > 0:
                put = _puts.set_index("expiration").copy()  # type: ignore
                put_atm_iv = put.query("`strike` == @atm_put_strike")[
                    "implied_volatility"
                ]
                if len(put_atm_iv) > 0:
                    put["ATM IV"] = put_atm_iv.iloc[0]
                    put["Skew"] = put["implied_volatility"] - put["ATM IV"]
                    put_skew = concat([put_skew, put])
        if call_skew.empty or put_skew.empty:
            raise OpenBBError(
                "Error: Not enough information to complete the operation. Likely due to zero values in the IV field."
            )
        call_skew = call_skew.set_index(["strike", "option_type"], append=True)
        put_skew = put_skew.set_index(["strike", "option_type"], append=True)
        skew_df = concat([call_skew, put_skew]).sort_index().reset_index()
        cols = ["Expiration", "Strike", "Option Type", "IV", "ATM IV", "Skew"]
        skew_df.columns = cols
        skew_df["Expiration"] = skew_df["Expiration"].astype(str)

        return skew_df