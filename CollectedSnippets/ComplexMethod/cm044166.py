def get_dateindex(self) -> list[datetime] | None:
        """Return the dateindex of the figure.

        Returns
        -------
        `list`
            The dateindex
        """
        # pylint: disable=import-outside-toplevel
        from numpy import datetime64
        from pandas import DatetimeIndex, to_datetime

        output: list[datetime] | None = None
        subplots = self.get_subplots_dict()

        try:
            false_y = list(self.select_traces(secondary_y=False))
            true_y = list(self.select_traces(secondary_y=True))
        except Exception:
            false_y = []
            true_y = []

        for trace in self.select_traces():
            if not hasattr(trace, "xaxis"):
                continue
            xref, yref = trace.xaxis, trace.yaxis
            row, col = subplots.get(xref, {}).get(yref, [(None, None)])[0]

            if trace.x is not None and len(trace.x) > 5:
                for x in trace.x[:2]:
                    if isinstance(x, (datetime, datetime64, DatetimeIndex)):
                        output = trace.x
                        name = trace.name if hasattr(trace, "name") else f"{trace}"

                        secondary_y: bool | None = trace in true_y
                        if trace not in (false_y + true_y):
                            secondary_y = None

                        self._date_xaxs[trace.xaxis] = {
                            "yaxis": trace.yaxis,
                            "name": name,
                            "row": row,
                            "col": col,
                            "secondary_y": secondary_y,
                        }
                        self._subplot_xdates.setdefault(row, {}).setdefault(
                            col, []
                        ).append(trace.x)

        # We convert the dateindex to a list of datetime objects if it's a numpy array
        if output is not None and isinstance(output[0], datetime64):
            output = (
                to_datetime(output).to_pydatetime().astype("datetime64[ms]").tolist()
            )

        return output