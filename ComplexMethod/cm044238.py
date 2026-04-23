def strategies(  # noqa: PLR0912
        self,
        days: list | None = None,
        straddle_strike: float | None = None,
        strangle_moneyness: list[float] | None = None,
        synthetic_longs: list[float] | None = None,
        synthetic_shorts: list[float] | None = None,
        vertical_calls: list[tuple] | None = None,
        vertical_puts: list[tuple] | None = None,
        underlying_price: float | None = None,
    ) -> "DataFrame":
        """
        Get options strategies for all, or a list of, DTE(s).
        Currently supports straddles, strangles, synthetic long and shorts, and vertical spreads.

        Multiple strategies, expirations, and % moneyness can be returned.

        A negative value for `straddle_strike` or `strangle_moneyness` returns short options.

        A synthetic long/short position is a bought/sold call and sold/bought put at the same strike.

        A sold call strike that is lower than the bought strike,
        or a sold put strike that is higher than the bought strike,
        is a bearish vertical spread.

        The default state returns a long straddle for each expiry.

        Parameters
        ----------
        days: list[int]
            List of DTE(s) to get strategies for. Enter a single value, or multiple as a list.
            Select all dates by entering, -1. Large chains may take a few seconds to process all dates.
            Defaults to [20,40,60,90,180,360].
        straddle_strike: float
            The target strike price for the straddle. Defaults to the last price of the underlying stock,
            and both strikes will always be on OTM side.
            Enter a strike price to force call and put strikes to be the same.
        strangle_moneyness: List[float]
            List of OTM moneyness to target, expressed as a percent value between 0 and 100.
            Enter a single value, or multiple as a list.
        synthetic_long: List[float]
            List of strikes for a synthetic long position.
        synthetic_short: List[float]
            List of strikes for a synthetic short position.
        vertical_calls: List[tuple]
            Call strikes for vertical spreads, entered as a list of paired tuples - [(sold strike, bought strike)].
        vertical_puts: List[float]
            Put strikes for vertical spreads, entered as a list of paired tuples - [(sold strike, bought strike)].
        underlying_price: Optional[float]
            Only supply this is if the underlying price is not a returned field.

        Returns
        -------
        DataFrame
            Pandas DataFrame with the results.
        """
        # pylint: disable=import-outside-toplevel
        from pandas import DataFrame, concat

        def to_clean_list(x):
            if x is None:
                return None
            return [x] if not isinstance(x, list) else x

        def split_into_tuples(x):
            """Split a list into paired tuples."""
            if x is None:
                return None
            if isinstance(x, tuple):
                return [x]
            if isinstance(x, list) and isinstance(x[0], tuple):
                return x
            paired_tuples: list = []
            for i in range(0, len(x), 2):
                paired_tuples.append((x[i], x[i + 1]))
            return paired_tuples

        # Check if all items are False
        if (  # pylint: disable=too-many-boolean-expressions
            straddle_strike is None
            and strangle_moneyness is None
            and synthetic_longs is None
            and synthetic_shorts is None
            and vertical_calls is None
            and vertical_puts is None
        ):
            straddle_strike = 0

        chains = self.dataframe
        bid = self._identify_price_col(chains, "call", "bid")
        chains = chains[chains[bid].notnull()].query("`dte` >= 0")
        days = (
            chains.dte.unique().tolist()
            if days == -1
            else days if days else [20, 40, 60, 90, 180, 360]
        )
        # Allows a single input to be passed instead of a list.
        days = [days] if isinstance(days, int) else days  # type: ignore[list-item]

        strangle_moneyness = strangle_moneyness or [0.0]
        strangle_moneyness = to_clean_list(strangle_moneyness)  # type: ignore
        synthetic_longs = to_clean_list(synthetic_longs)  # type: ignore
        synthetic_shorts = to_clean_list(synthetic_shorts)  # type: ignore
        vertical_calls = split_into_tuples(vertical_calls)  # type: ignore
        vertical_puts = split_into_tuples(vertical_puts)  # type: ignore

        days_list: list = []
        strategies: DataFrame = DataFrame()
        straddles: DataFrame = DataFrame()
        strangles: DataFrame = DataFrame()
        strangles_: DataFrame = DataFrame()
        synthetic_longs_df: DataFrame = DataFrame()
        _synthetic_longs: DataFrame = DataFrame()
        synthetic_shorts_df: DataFrame = DataFrame()
        _synthetic_shorts: DataFrame = DataFrame()
        call_spreads: DataFrame = DataFrame()
        put_spreads: DataFrame = DataFrame()

        # Get the nearest expiration date for each supplied date and
        # discard any duplicates found - i.e, [29,30] will yield only one result.
        for day in days:  # type: ignore
            _day = day or -1
            days_list.append(self._get_nearest_expiration(_day))
        days = sorted(set(days_list))

        if vertical_calls is not None:
            for c in vertical_calls:
                c_strike1 = c[0]
                c_strike2 = c[1]
                for day in days:
                    call_spread = self.vertical_call_spread(
                        day, c_strike1, c_strike2, underlying_price
                    )
                    if not call_spread.empty:
                        call_spreads = concat([call_spreads, call_spread.transpose()])

        if vertical_puts:
            for c in vertical_puts:
                p_strike1 = c[0]
                p_strike2 = c[1]
            for day in days:
                put_spread = self.vertical_put_spread(
                    day, p_strike1, p_strike2, underlying_price
                )
                if not put_spread.empty:
                    put_spreads = concat([put_spreads, put_spread.transpose()])

        if straddle_strike or straddle_strike == 0:
            straddle_strike = None if straddle_strike == 0 else straddle_strike
            for day in days:
                straddle = self.straddle(
                    day, straddle_strike, underlying_price
                ).transpose()
                if not straddle.empty and straddle.iloc[0]["Cost"] != 0:
                    straddles = concat([straddles, straddle])

        if strangle_moneyness and strangle_moneyness[0] != 0:
            for day in days:
                for moneyness in strangle_moneyness:
                    strangle = self.strangle(
                        day, moneyness, underlying_price
                    ).transpose()
                    if strangle.iloc[0]["Cost"] != 0:
                        strangles_ = concat([strangles_, strangle])

            strangles = concat([strangles, strangles_])
            strangles = strangles.query("`Strike 1` != `Strike 2`").drop_duplicates()

        if synthetic_longs:
            strikes = synthetic_longs
            for day in days:
                for strike in strikes:
                    _synthetic_long = self.synthetic_long(
                        day, strike, underlying_price
                    ).transpose()
                    if (
                        not _synthetic_long.empty
                        and _synthetic_long.iloc[0]["Strike 1 Premium"] != 0
                    ):
                        _synthetic_longs = concat([_synthetic_longs, _synthetic_long])

            synthetic_longs_df = concat([synthetic_longs_df, _synthetic_longs])

        if synthetic_shorts:
            strikes = synthetic_shorts
            for day in days:
                for strike in strikes:
                    _synthetic_short = self.synthetic_short(
                        day, strike, underlying_price
                    ).transpose()
                    if (
                        not _synthetic_short.empty
                        and _synthetic_short.iloc[0]["Strike 1 Premium"] != 0
                    ):
                        _synthetic_shorts = concat(
                            [_synthetic_shorts, _synthetic_short]
                        )

            if not _synthetic_shorts.empty:
                synthetic_shorts_df = concat([synthetic_shorts_df, _synthetic_shorts])

        strategies = concat(
            [
                straddles,
                strangles,
                synthetic_longs_df,
                synthetic_shorts_df,
                call_spreads,
                put_spreads,
            ]
        )

        if strategies.empty:
            raise OpenBBError("No strategies found for the given parameters.")

        strategies = strategies.reset_index().rename(columns={"index": "Strategy"})
        strategies = (
            strategies.set_index(["Expiration", "DTE"])
            .sort_index()
            .drop(columns=["Symbol"])
        )
        return strategies.reset_index()