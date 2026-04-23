def get_subplot(self, subplot: str) -> bool:
        """Return True if subplots will be able to be plotted with current data."""
        if subplot == "volume":
            return self.show_volume

        if subplot in ["ad", "adosc", "obv", "vwap"] and not self.has_volume:
            self.indicators.remove_indicator(subplot)
            warnings.warn(
                f"[bold red]Warning:[/] [yellow]{subplot.upper()}"
                " requires volume data to be plotted but no volume data was found."
                " Indicator will not be plotted.[/]"
            )
            return False

        output = False

        try:
            indicator = self.indicators.get_indicator(subplot)
            if indicator is None:
                return False

            output = self.indicators.get_indicator_data(
                self.df_stock.copy(),  # type: ignore
                indicator,
                **self.indicators.get_options_dict(indicator.name) or {},
            )
            if not isinstance(output, bool):
                output = output.dropna()  # type: ignore

                if output is None or output.empty:
                    output = False

            return True

        except Exception:
            output = False

        return output