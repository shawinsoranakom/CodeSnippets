def process_fig(self, fig: OpenBBFigure, volume_ticks_x: int = 7) -> OpenBBFigure:
        """Process plotly figure before plotting indicators.

        Parameters
        ----------
        fig : OpenBBFigure
            Plotly figure to process
        volume_ticks_x : int, optional
            Number to multiply volume, by default 7

        Returns
        -------
        fig : OpenBBFigure
            Processed plotly figure
        """
        new_subplot = OpenBBFigure(charting_settings=self.charting_settings)
        new_subplot = fig.create_subplots(
            shared_xaxes=True, **self.get_fig_settings_dict()
        )
        subplots: dict[str, dict[str, list[Any]]] = {}
        grid_ref = fig._validate_get_grid_ref()  # pylint: disable=protected-access
        for r, plot_row in enumerate(grid_ref):
            for c, plot_refs in enumerate(plot_row):
                if not plot_refs:
                    continue
                for subplot_ref in plot_refs:
                    if subplot_ref.subplot_type == "xy":
                        xaxis, yaxis = subplot_ref.layout_keys
                        xref = xaxis.replace("axis", "")
                        yref = yaxis.replace("axis", "")
                        row = r + 1
                        col = c + 1
                        subplots.setdefault(xref, {}).setdefault(yref, []).append(
                            (row, col)
                        )

        for trace in fig.select_traces():
            xref, yref = trace.xaxis, trace.yaxis
            row, col = subplots[xref][yref][0]
            new_subplot.add_trace(trace, row=row, col=col, secondary_y=False)

        fig_json = fig.to_plotly_json()["layout"]
        for layout in fig_json:
            if (
                isinstance(fig_json[layout], dict)
                and "domain" in fig_json[layout]
                and any(x in layout for x in ["xaxis", "yaxis"])
            ):
                fig_json[layout]["domain"] = new_subplot.to_plotly_json()["layout"][
                    layout
                ]["domain"]

            fig.layout.update({layout: fig_json[layout]})  # type: ignore
            new_subplot.layout.update({layout: fig.layout[layout]})  # type: ignore

        if self.show_volume:
            new_subplot.add_inchart_volume(
                self.df_stock,
                self.close_column,
                volume_ticks_x=volume_ticks_x,  # type: ignore
            )

        return new_subplot