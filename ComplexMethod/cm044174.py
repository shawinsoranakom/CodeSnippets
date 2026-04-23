def plot_fig(  # noqa: PLR0912
        self,
        fig: OpenBBFigure | None = None,
        symbol: str = "",
        candles: bool = True,
        volume_ticks_x: int = 7,
    ) -> OpenBBFigure:
        """Plot indicators on plotly figure.

        Parameters
        ----------
        fig : OpenBBFigure, optional
            Plotly figure to plot indicators on, by default None
        symbol : str, optional
            Symbol to plot, by default uses the dataframe.name attribute if available or ""
        candles : bool, optional
            Plot a candlestick chart, by default True (if False, plots a line chart)
        volume_ticks_x : int, optional
            Number to multiply volume, by default 7

        Returns
        -------
        fig : OpenBBFigure
            Plotly figure with candlestick/line chart and volume bar chart (if enabled)
        """
        self.df_ta = self.calculate_indicators()

        symbol = self.df_stock.name if hasattr(self.df_stock, "name") and not symbol else symbol  # type: ignore

        figure = self.init_plot(symbol, candles) if fig is None else fig
        subplot_row, fig_new = 2, {}
        inchart_index, ma_done = 0, False

        figure = self.process_fig(figure, volume_ticks_x)

        # Aroon indicator is always plotted first since it has 2 subplot rows.
        # ATR messes up the volume layout so we plot it last.
        plot_indicators = sorted(
            self.indicators.get_active_ids(),
            key=lambda x: (
                50
                if x == "aroon"
                else 1000 if x == "atr" else 999 if x in self.subplots else 1
            ),
        )

        for indicator in plot_indicators:
            try:
                if indicator in self.subplots:
                    figure, subplot_row = getattr(self, f"plot_{indicator}")(
                        figure, self.df_ta, subplot_row
                    )
                elif indicator in self.ma_mode or indicator in self.inchart:
                    if indicator in self.ma_mode:
                        if ma_done:
                            continue
                        indicator, ma_done = "ma", True  # noqa

                    figure, inchart_index = getattr(self, f"plot_{indicator}")(
                        figure, self.df_ta, inchart_index
                    )
                    figure.layout.annotations = None
                elif indicator in ["fib", "srlines", "demark", "clenow", "ichimoku"]:
                    figure = getattr(self, f"plot_{indicator}")(figure, self.df_ta)
                else:
                    raise ValueError(f"Unknown indicator: {indicator}")

                fig_new.update(figure.to_plotly_json())

                remaining_subplots = (
                    list(
                        set(plot_indicators[plot_indicators.index(indicator) + 1 :])
                        - set(self.inchart)
                    )
                    if indicator != "ma"
                    else []
                )
                if subplot_row > 5 and remaining_subplots:
                    warnings.warn(
                        f"[bold red]Reached max number of subplots.   Skipping {', '.join(remaining_subplots)}[/]"
                    )
                    break
            except Exception as e:
                warnings.warn(f"[bold red]Error plotting {indicator}: {e}[/]")
                continue

        for row in range(0, subplot_row + 1):
            figure.update_yaxes(
                row=row,
                col=1,
                secondary_y=False,
                nticks=15 if subplot_row < 3 else 6,
                tickfont=dict(size=12),
            )
        figure.update_traces(
            selector=dict(type="scatter", mode="lines"), connectgaps=True
        )
        if hasattr(figure, "hide_holidays"):
            figure.hide_holidays(self.prepost)  # type: ignore

        if not self.show_volume:
            figure.update_layout(margin=dict(l=20))

        # We remove xaxis labels from all but bottom subplot,
        # and we make sure they all match the bottom one
        xbottom = f"y{subplot_row + 1}"
        xaxes = list(figure.select_xaxes())
        for xa in xaxes:
            if xa == xaxes[-1]:
                xa.showticklabels = True
            if not xa.showticklabels and xa.anchor != xbottom:
                xa.showticklabels = False
            if xa.anchor != xbottom:
                xa.matches = xbottom.replace("y", "x")

        fib_legend_shown = False
        sr_legend_shown = False
        for item in figure.data:
            if item.name:
                item.name = item.name.replace("_", " ")
                if "MA " not in item.name:
                    item.showlegend = False
                if "<b>" in item.name:
                    item.name = "Fib"
                    item.hoverinfo = "none"
                    item.hoveron = "fills"
                    item.pop("hovertemplate", None)
                    item.legendgroup = "Fib"
                    if not fib_legend_shown:
                        item.showlegend = True
                        fib_legend_shown = True
                if (
                    "Historical" not in item.name
                    and "Candlestick" not in item.name
                    and "Fib" not in item.name
                    and item.name is not None
                ):
                    if (
                        "MA " in item.name
                        or "VWAP" in item.name
                        or "DC" in item.name
                        or "KC" in item.name
                        or "-sen" in item.name
                        or "Senkou" in item.name
                    ):
                        item.showlegend = True
                        item.hoverinfo = "y"
                        item.hovertemplate = "%{fullData.name}:%{y}<extra></extra>"
                    else:
                        item.hovertemplate = "%{y}<extra></extra>"
            if item.name is None:
                item.name = "SR Lines"
                item.hoverinfo = "none"
                item.hoveron = "fills"
                item.legendgroup = "SR Lines"
                item.pop("hovertemplate", None)
                item.opacity = 0.5
                if not sr_legend_shown:
                    item.showlegend = True
                    sr_legend_shown = True

        if "annotations" in figure.layout:
            for item in figure.layout.annotations:  # type: ignore
                item["font"]["size"] = 14
        figure.update_layout(margin=dict(l=50, r=10, b=10, t=20))
        return figure