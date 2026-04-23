def _get_nearest_strike(
        self,
        option_type: Literal["call", "put"],
        days: int | str | None = None,
        strike: float | None = None,
        price_col: str | None = None,
        force_otm: bool = True,
    ) -> float | None:
        """
        Get the strike to the target option type, price, and number of days until expiry.
        This method is not intended to be called directly.

        Parameters
        ----------
        option_type: Literal["call", "put"]
            The option type to use when selecting the bid or ask price.
        days: int
            The target number of days until expiry.  Default is 30 days.
        strike: float
            The target strike price.  Default is the last price of the underlying stock.
        price_col: str
            The price column to use for the calculation.
        force_otm: bool
            If True, the nearest OTM strike is returned.  Default is True.

        Returns
        -------
        float
            The closest strike price to the target price and number of days until expiry.
        """
        # pylint: disable=import-outside-toplevel
        from pandas import Series

        if option_type not in ["call", "put"]:
            raise OpenBBError("Error: option_type must be either 'call' or 'put'")

        chains = self.dataframe
        days = -1 if days == 0 else days

        if days is None:
            days = 30

        dte_estimate = self._get_nearest_expiration(days)
        df = (
            chains[chains.expiration.astype(str) == dte_estimate]
            .query("`option_type` == @option_type")
            .copy()
        )
        if strike is None:
            strike = df.underlying_price.iloc[0]

        if price_col is not None:
            df = df[df[price_col].notnull()]  # type: ignore

        if df.empty or len(df) == 0:
            return None

        if force_otm is False:
            strikes = Series(df.strike.unique().tolist())
            nearest = (strikes - strike).abs().idxmin()
            return strikes.iloc[nearest]

        nearest = (
            df[df.strike <= strike] if option_type == "put" else df[df.strike >= strike]
        )

        if nearest.empty or len(nearest) == 0:  # type: ignore
            return None

        nearest = (
            nearest.query("strike.idxmax()")  # type: ignore
            if option_type == "put"
            else nearest.query("strike.idxmin()")  # type: ignore
        )

        return nearest.strike