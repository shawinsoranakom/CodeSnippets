def add_histplot(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        dataset: Union["ndarray", "Series", TimeSeriesT],
        name: str | list[str] | None = None,
        colors: list[str] | None = None,
        bins: int | str = 15,
        curve: Literal["normal", "kde"] = "normal",
        show_curve: bool = True,
        show_rug: bool = True,
        show_hist: bool = True,
        forecast: bool = False,
        row: int = 1,
        col: int = 1,
    ) -> None:
        """Add a histogram with a curve and rug plot if desired.

        Parameters
        ----------
        dataset : `Union[ndarray, Series, TimeSeriesT]`
            Data to plot
        name : `Optional[Union[str, List[str]]]`, optional
            Name of the plot, by default None
        colors : `Optional[List[str]]`, optional
            Colors of the plot, by default None
        bins : `Union[int, str]`, optional
            Number of bins, by default 15
        curve : `Literal["normal", "kde"]`, optional
            Type of curve to plot, by default "normal"
        show_curve : `bool`, optional
            Whether to show the curve, by default True
        show_rug : `bool`, optional
            Whether to show the rug plot, by default True
        show_hist : `bool`, optional
            Whether to show the histogram, by default True
        forecast : `bool`, optional
            Whether the data is a darts forecast TimeSeries, by default False
        row : `int`, optional
            Row of the subplot, by default 1
        col : `int`, optional
            Column of the subplot, by default 1
        """
        # pylint: disable=import-outside-toplevel
        from numpy import linspace, mean, ndarray, std
        from pandas import Series
        from scipy import stats

        callback = stats.norm if curve == "normal" else stats.gaussian_kde

        def _validate_x(data: ndarray | Series | type[TimeSeriesT]):
            if forecast:
                data = data.univariate_values()  # type: ignore
            if isinstance(data, Series):
                data = data.to_numpy()
            if isinstance(data, ndarray):
                data = data.tolist()
            if isinstance(data, list):
                data = [data]  # type: ignore

            return data

        valid_x = _validate_x(dataset)

        if isinstance(name, str):
            name = [name]

        if isinstance(colors, str):
            colors = [colors]
        if not name:
            name = [None] * len(valid_x)  # type: ignore
        if not colors:
            colors = [None] * len(valid_x)  # type: ignore

        max_y = 0
        for i, (x_i, name_i, color_i) in enumerate(zip(valid_x, name, colors)):  # type: ignore
            if not color_i:
                color_i = (  # noqa: PLW2901
                    self._theme.up_color if i % 2 == 0 else self._theme.down_color
                )

            res_mean, res_std = mean(x_i), std(x_i)
            res_min, res_max = min(x_i), max(x_i)
            x = linspace(res_min, res_max, 100)
            if show_hist:
                if forecast:
                    components = list(dataset.components[:4])  # type: ignore
                    values = dataset[components].all_values(copy=False).flatten(order="F")  # type: ignore
                    n_components = len(components)
                    n_entries = len(values) // n_components
                    for i2, label in zip(range(n_components), components):
                        self.add_histogram(
                            x=values[
                                i2 * n_entries : (i2 + 1) * n_entries
                            ],  # noqa: E203  # noqa: E203
                            name=label,
                            marker_color=color_i,
                            nbinsx=bins,
                            opacity=0.7,
                            row=row,
                            col=col,
                        )
                else:
                    self.add_histogram(
                        x=x_i,
                        name=name_i,
                        marker_color=color_i,
                        nbinsx=bins,
                        histnorm="probability density",
                        histfunc="sum",
                        opacity=0.7,
                        row=row,
                        col=col,
                    )

            if show_rug:
                self.add_scatter(
                    x=x_i,
                    y=[0.00002] * len(x_i),
                    name=name_i if len(name) < 2 else name[1],  # type: ignore
                    mode="markers",
                    marker=dict(
                        color=self._theme.down_color,
                        symbol="line-ns-open",
                        size=10,
                    ),
                    row=row,
                    col=col,
                )
            if show_curve:
                # type: ignore
                if curve == "kde":
                    curve_x = [None] * len(valid_x)
                    curve_y = [None] * len(valid_x)
                    # pylint: disable=consider-using-enumerate
                    for index in range(len(valid_x)):
                        curve_x[index] = [res_min + xx * (res_max - res_min) / 500 for xx in range(500)]  # type: ignore
                        curve_y[index] = stats.gaussian_kde(valid_x[index])(
                            curve_x[index]
                        )
                    for index in range(len(valid_x)):
                        self.add_scatter(
                            x=curve_x[index],  # type: ignore
                            y=curve_y[index],  # type: ignore
                            name=name_i,
                            mode="lines",
                            showlegend=False,
                            marker=dict(color=color_i),
                            row=row,
                            col=col,
                        )
                        max_y = max(max_y, max(curve_y[index]) * 1.2)  # type: ignore

                else:
                    y = (
                        callback(res_mean, res_std).pdf(x)  # type: ignore
                        * len(valid_x[0])
                        * (res_max - res_min)
                        / bins
                    )

                    self.add_scatter(
                        x=x,
                        y=y,
                        name=name_i,
                        mode="lines",
                        marker=dict(color=color_i),
                        showlegend=False,
                        row=row,
                        col=col,
                    )

                    max_y = max(max_y, y * 2)

        self.update_yaxes(
            position=0.0,
            range=[0, max_y],
            row=row,
            col=col,
            automargin=False,
            autorange=False,
        )

        self.update_layout(barmode="overlay", bargap=0.01, bargroupgap=0)