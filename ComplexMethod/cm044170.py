def get_indicator_data(self, indicator: TAIndicator, **args) -> "DataFrame":
        """
        Return dataframe with indicator data.

        Parameters
        ----------
        indicator : TAIndicator
            TAIndicator object
        args : dict
            Arguments for given indicator

        Return
        -------
        DataFrame
            Dataframe with indicator data
        """
        # pylint: disable=import-outside-toplevel
        import pandas_ta as ta
        from pandas import DataFrame

        output = None
        if indicator and indicator.name in self.ma_mode:
            if isinstance(indicator.get_argument_values("length"), list):
                df_ta = DataFrame()

                for length in indicator.get_argument_values("length"):
                    df_ma = getattr(ta, indicator.name)(
                        self.df_ta[self.close_col], length=length
                    )
                    df_ta.insert(0, f"{indicator.name.upper()}_{length}", df_ma)

                output = df_ta

            else:
                output = getattr(ta, indicator.name)(
                    self.df_ta[self.close_col],
                    length=indicator.get_argument_values("length"),
                )
                if indicator.name == "zlma" and output is not None:
                    output.name = output.name.replace("ZL_EMA", "ZLMA")

        elif indicator.name == "vwap":
            ta_columns = self.columns[indicator.name]
            ta_columns = [self.df_ta[col] for col in ta_columns]  # type: ignore

            output = getattr(ta, indicator.name)(
                *ta_columns,
            )
        elif indicator.name in self.columns:
            ta_columns = self.columns[indicator.name]
            ta_columns = [self.df_ta[col] for col in ta_columns]  # type: ignore

            if indicator.get_argument_values("use_open") is True:
                ta_columns.append(self.df_ta["open"])

            output = getattr(ta, indicator.name)(*ta_columns, **args)
        else:
            output = getattr(ta, indicator.name)(self.df_ta[self.close_col], **args)

        # Drop NaN values from output and return None if empty
        if output is not None:
            output.dropna(inplace=True)
            if output.empty:
                output = None

        return output