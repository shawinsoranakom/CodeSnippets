def add_corr_plot(  # pylint: disable=too-many-arguments
        self,
        series: "DataFrame",
        max_lag: int = 20,
        m: int | None = None,
        alpha: float | None = 0.05,
        marker: dict | None = None,
        row: int | None = None,
        col: int | None = None,
        pacf: bool = False,
        **kwargs,
    ) -> None:
        """Add a correlation plot to a figure object.

        Parameters
        ----------
        fig : OpenBBFigure
            Figure object to add plot to
        series : DataFrame
            Dataframe to look at
        max_lag : int, optional
            Number of lags to look at, by default 15
        m: Optional[int]
            Optionally, a time lag to highlight on the plot. Default is none.
        alpha: Optional[float]
            Optionally, a significance level to highlight on the plot. Default is 0.05.
        row : int, optional
            Row to add plot to, by default None
        col : int, optional
            Column to add plot to, by default None
        pacf : bool, optional
            Flag to indicate whether to use partial autocorrelation or not, by default False
        """
        # pylint: disable=import-outside-toplevel
        import statsmodels.api as sm  # noqa
        from numpy import arange, asanyarray, ceil, log10, isscalar  # noqa

        mode = "markers+lines" if marker else "lines"
        line = kwargs.pop("line", None)

        def _prepare_data_corr_plot(x, lags):
            zero = True
            irregular = False
            if lags is None:
                # GH 4663 - use a sensible default value
                nobs = x.shape[0]
                lim = min(int(ceil(10 * log10(nobs))), nobs - 1)
                lags = arange(not zero, lim + 1)
            elif isscalar(lags):
                lags = arange(
                    not zero,
                    int(lags) + 1,  # type: ignore
                )  # +1 for zero lag
            else:
                irregular = True
                lags = asanyarray(lags).astype(int)
            nlags = lags.max(0)

            return lags, nlags, irregular

        lags, nlags, irregular = _prepare_data_corr_plot(series, max_lag)

        callback = sm.tsa.stattools.pacf if pacf else sm.tsa.stattools.acf
        if not pacf:
            kwargs.update(dict(fft=False))

        acf_x = callback(
            series,  # type: ignore
            nlags=nlags,
            alpha=alpha,
            **kwargs,
        )

        acf_x, confint = acf_x[:2] if not pacf else acf_x  # type: ignore

        if irregular:
            acf_x = acf_x[lags]

        try:
            confint = confint[lags]
            if lags[0] == 0:
                lags = lags[1:]
                confint = confint[1:]
                acf_x = acf_x[1:]
            lags = lags.astype(float)
            lags[0] -= 0.5
            lags[-1] += 0.5

            upp_band = confint[:, 0] - acf_x
            low_band = confint[:, 1] - acf_x

            # pylint: disable=C0200
            for x in range(len(acf_x)):
                self.add_scatter(
                    x=(x, x),
                    y=(0, acf_x[x]),
                    mode=mode,
                    marker=marker,
                    line=line,
                    line_width=(2 if m is not None and x == m else 1),
                    row=row,
                    col=col,
                )

            self.add_scatter(
                x=lags,
                y=upp_band,
                mode="lines",
                line_color="rgba(0, 0, 0, 0)",
                opacity=0,
                row=row,
                col=col,
            )

            self.add_scatter(
                x=lags,
                y=low_band,
                mode="lines",
                fillcolor="rgba(255, 217, 0, 0.30)",
                fill="tonexty",
                line_color="rgba(0, 0, 0, 0.0)",
                opacity=0,
                row=row,
                col=col,
            )
            self.add_scatter(
                x=[0, max_lag + 1],
                y=[0, 0],
                mode="lines",
                line_color="white",
                row=row,
                col=col,
            )
            self.update_traces(showlegend=False)

        except ValueError:
            pass