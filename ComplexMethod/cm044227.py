def dataframe(self) -> "DataFrame":
        """Return all data as a Pandas DataFrame,
        with additional computed columns (Breakeven, GEX, DEX) if available.
        """
        # pylint: disable=import-outside-toplevel
        from numpy import nan
        from pandas import DataFrame, DatetimeIndex, Timedelta, concat, to_datetime

        chains_data = DataFrame(
            self.model_dump(
                exclude_unset=True,
                exclude_none=True,
            )
        )

        if "underlying_price" not in chains_data.columns and not self.last_price:
            raise OpenBBError(
                "'underlying_price' was not returned in the provider data."
                + "\n\n Please set the 'last_price' property and try again."
                + "\n\n Note: This error does not impact the standard OBBject `to_df()` method."
            )

        # Add the underlying price to the DataFrame, or override the existing price.
        if self.last_price:
            chains_data["underlying_price"] = self.last_price

        if chains_data.empty:
            raise OpenBBError("Error: No validated data was found.")

        if "dte" not in chains_data.columns and "eod_date" in chains_data.columns:
            _date = to_datetime(chains_data.eod_date)
            temp = DatetimeIndex(chains_data.expiration)
            temp_ = temp - _date  # type: ignore
            chains_data["dte"] = [Timedelta(_temp_).days for _temp_ in temp_]

        if "dte" in chains_data.columns:
            chains_data = DataFrame(chains_data[chains_data.dte >= 0])

        if "dte" not in chains_data.columns and "eod_date" not in chains_data.columns:
            today = datetime.today().date()
            chains_data["dte"] = chains_data.expiration - today

        # Add the breakeven price for each option, and the DEX and GEX for each option, if available.
        try:
            _calls = DataFrame(chains_data[chains_data.option_type == "call"])
            _puts = DataFrame(chains_data[chains_data.option_type == "put"])
            _ask = self._identify_price_col(
                chains_data, "call", "ask"
            )  # pylint: disable=W0212
            _calls.loc[:, ("Breakeven")] = _calls.strike + _calls.loc[:, (_ask)]
            _puts.loc[:, ("Breakeven")] = _puts.strike - _puts.loc[:, (_ask)]
            if "delta" in _calls.columns:
                _calls.loc[:, ("DEX")] = (
                    (
                        _calls.delta
                        * (
                            _calls.contract_size
                            if hasattr(_calls, "contract_size")
                            else 100
                        )
                        * _calls.open_interest
                        * _calls.underlying_price
                    )
                    .replace({nan: 0})
                    .astype("int64")
                )
                _puts.loc[:, ("DEX")] = (
                    (
                        _puts.delta
                        * (
                            _puts.contract_size
                            if hasattr(_puts, "contract_size")
                            else 100
                        )
                        * _puts.open_interest
                        * _puts.underlying_price
                    )
                    .replace({nan: 0})
                    .astype("int64")
                )

            if "gamma" in _calls.columns:
                _calls.loc[:, ("GEX")] = (
                    (
                        _calls.gamma
                        * (
                            _calls.contract_size
                            if hasattr(_calls, "contract_size")
                            else 100
                        )
                        * _calls.open_interest
                        * (_calls.underlying_price * _calls.underlying_price)
                        * 0.01
                    )
                    .replace({nan: 0})
                    .astype("int64")
                )
                _puts.loc[:, ("GEX")] = (
                    (
                        _puts.gamma
                        * (
                            _puts.contract_size
                            if hasattr(_puts, "contract_size")
                            else 100
                        )
                        * _puts.open_interest
                        * (_puts.underlying_price * _puts.underlying_price)
                        * 0.01
                        * (-1)
                    )
                    .replace({nan: 0})
                    .astype("int64")
                )

            _calls.set_index(keys=["expiration", "strike", "option_type"], inplace=True)
            _puts.set_index(keys=["expiration", "strike", "option_type"], inplace=True)
            df = concat([_puts, _calls])
            df = df.sort_index().reset_index()

            return df

        except Exception:  # pylint: disable=broad-exception-caught
            return chains_data