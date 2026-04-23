def filter_data(
        self,
        date: str | int | None = None,
        option_type: Literal["call", "put"] | None = None,
        moneyness: Literal["otm", "itm"] | None = None,
        column: str | None = None,
        value_min: float | None = None,
        value_max: float | None = None,
        stat: Literal["open_interest", "volume", "dex", "gex"] | None = None,
        by: Literal["expiration", "strike"] = "expiration",
    ) -> "DataFrame":
        """Return statistics by strike or expiration; or, the filtered chains data.

        Parameters
        ----------
        date: Optional[Union[str, int]]
            The expiration date, or days until expiry, to use. This is applied before any filters.
        option_type: Optional[Literal["call", "put"]]
            The option type to filter by, None returns both.
            This is ignored if stat is not None.
        moneyness: Optional[Literal["otm", "itm"]]
            The moneyness to filter by, None returns both.
        column: Optional[str]
            The column to filter by.
            If no min/max are supplied it will sort all data by this column, in descending order.
            This is ignored if stat is not None.
        value_min: Optional[float]
            The minimum value to filter by. Column must be numeric.
            This is ignored if stat is not None.
        value_max: Optional[float]
            The maximum value to filter by. Column must be numeric.
            This is ignored if stat is not None.
        stat: Optional[Literal["open_interest", "volume", "dex", "gex"]]
            The statistical metric to filter by.
            Other fields are ignored if this is not None.
        by: Literal["expiration", "strike"]
            Filter the `stat` by expiration or strike, default is "expiration".
            If a date is supplied, "strike" is always returned.
            This is ignored if `stat` is None.
        """
        # pylint: disable=import-outside-toplevel
        from numpy import nan
        from pandas import DataFrame, concat

        stats = ["open_interest", "volume", "dex", "gex"]
        _stat = stat.upper() if stat in ["dex", "gex"] else stat
        by = "strike" if date is not None else by
        if stat is not None:
            if stat not in stats:
                raise OpenBBError(f"Error: stat must be one of {stats}")
            if stat in ["volume", "open_interest"]:
                return DataFrame(self._get_stat(stat, moneyness=moneyness, date=date)[by]).replace({nan: None})  # type: ignore
            if (
                _stat not in self.dataframe.columns
                and self.has_greeks
                and "underlying_price" not in self.dataframe.columns
            ):
                raise OpenBBError(
                    f"Error: '{stat}' could not be generated because"
                    + " the underlying price was not returned by the provider."
                    + " Set manually with 'underlying_price' property."
                )
            df = DataFrame(self._get_stat(_stat, moneyness=moneyness, date=date)[by])  # type: ignore
            return df.replace({nan: None})

        df = self.dataframe

        if moneyness is not None:
            df_calls = DataFrame(
                df[df.strike >= df.underlying_price].query("option_type == 'call'")
            )
            df_puts = DataFrame(
                df[df.strike <= df.underlying_price].query("option_type == 'put'")
            )
            df = concat([df_calls, df_puts])

        if date is not None:
            date = self._get_nearest_expiration(date)
            df = DataFrame(df[df.expiration.astype(str) == date])

        if option_type is not None:
            df = DataFrame(df[df.option_type == option_type])

        if column is not None:
            if column not in df.columns:
                raise OpenBBError(f"Error: column '{column}' not found in data")
            df = DataFrame(df[df[column].notnull()])
            if value_min is not None and value_max is not None:
                df = DataFrame(
                    df[
                        (df[column].abs() >= value_min)
                        & (df[column].abs() <= value_max)
                    ]
                )
            elif value_min is not None:
                df = DataFrame(df[df[column].abs() >= value_min])
            elif value_max is not None:
                df = DataFrame(df[df[column].abs() <= value_max])
            else:
                df = DataFrame(df.sort_values(by=column, ascending=False))

        return df.reset_index(drop=True)