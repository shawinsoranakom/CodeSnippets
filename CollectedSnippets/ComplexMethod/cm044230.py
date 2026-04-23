def _get_nearest_otm_strikes(
        self,
        date: str | int | None = None,
        underlying_price: float | None = None,
        moneyness: float | None = None,
    ) -> dict:
        """Get the nearest put and call strikes at a given percent OTM from the underlying price.
        This method is not intended to be called directly.

        Parameters
        ----------
        date: Optional[Union[str, int]]
            The expiration date, or days until expiry, to use.
        moneyness: Optional[float]
            The target percent OTM, expressed as a percent between 0 and 100.  Default is 0.25%.
        underlying_price: Optional[float]
            Only supply this is if the underlying price is not a returned field.

        Returns
        -------
        Dict[str, float]
            Dictionary of the upper (call) and lower (put) strike prices.
        """
        # pylint: disable=import-outside-toplevel
        from pandas import Series

        if moneyness is None:
            moneyness = 0.25

        if 0 < moneyness < 100:
            moneyness = moneyness / 100

        if moneyness > 100 or moneyness < 0:
            raise OpenBBError(
                "Error: Moneyness must be expressed as a percentage between 0 and 100"
            )

        df = self.dataframe

        if underlying_price is None and not hasattr(df, "underlying_price"):
            raise OpenBBError(
                "Error: underlying_price must be provided if underlying_price is not available"
            )

        if date is not None:
            date = self._get_nearest_expiration(date)
            df = df[df.expiration.astype(str) == date]
            strikes = Series(df.strike.unique().tolist())

        last_price = (
            underlying_price
            if underlying_price is not None
            else df.underlying_price.iloc[0]
        )
        strikes = Series(self.strikes)

        upper = last_price * (1 + moneyness)  # type: ignore
        lower = last_price * (1 - moneyness)  # type: ignore
        nearest_call = (upper - strikes).abs().idxmin()
        call = strikes[nearest_call]
        nearest_put = (lower - strikes).abs().idxmin()
        put = strikes[nearest_put]
        otm_strikes = {"call": call, "put": put}

        return otm_strikes