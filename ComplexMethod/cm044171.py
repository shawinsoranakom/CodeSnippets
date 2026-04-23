def to_dataframe(self) -> "DataFrame":
        """Return dataframe with all indicators."""
        active_indicators = self.indicators.get_indicators()

        if not active_indicators:
            return None

        output = self.df_ta
        for indicator in active_indicators:
            if (
                indicator.name in self.columns
                and "volume" in self.columns[indicator.name]
                and not self.has_volume
            ):
                continue
            if indicator.name in ["fib", "srlines", "clenow", "demark", "ichimoku"]:
                continue
            try:
                indicator_data = self.get_indicator_data(
                    indicator,
                    **self.indicators.get_options_dict(indicator.name) or {},
                )
            except Exception as e:
                indicator_data = None
                raise TA_DataException(
                    f"Error processing indicator {indicator.name}: {e}"
                ) from e

            if indicator_data is not None:
                output = output.join(indicator_data).infer_objects()
                numeric_cols = output.select_dtypes(include=["number"]).columns
                output[numeric_cols] = output[numeric_cols].interpolate("linear")

        return output