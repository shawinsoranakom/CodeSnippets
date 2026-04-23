def plot(
        self,
        *,
        ax=None,
        n_cols=3,
        line_kw=None,
        ice_lines_kw=None,
        pd_line_kw=None,
        contour_kw=None,
        bar_kw=None,
        heatmap_kw=None,
        pdp_lim=None,
        centered=False,
    ):
        """Plot partial dependence plots.

        Parameters
        ----------
        ax : Matplotlib axes or array-like of Matplotlib axes, default=None
            - If a single axis is passed in, it is treated as a bounding axes
                and a grid of partial dependence plots will be drawn within
                these bounds. The `n_cols` parameter controls the number of
                columns in the grid.
            - If an array-like of axes are passed in, the partial dependence
                plots will be drawn directly into these axes.
            - If `None`, a figure and a bounding axes is created and treated
                as the single axes case.

        n_cols : int, default=3
            The maximum number of columns in the grid plot. Only active when
            `ax` is a single axes or `None`.

        line_kw : dict, default=None
            Dict with keywords passed to the `matplotlib.pyplot.plot` call.
            For one-way partial dependence plots.

        ice_lines_kw : dict, default=None
            Dictionary with keywords passed to the `matplotlib.pyplot.plot` call.
            For ICE lines in the one-way partial dependence plots.
            The key value pairs defined in `ice_lines_kw` takes priority over
            `line_kw`.

            .. versionadded:: 1.0

        pd_line_kw : dict, default=None
            Dictionary with keywords passed to the `matplotlib.pyplot.plot` call.
            For partial dependence in one-way partial dependence plots.
            The key value pairs defined in `pd_line_kw` takes priority over
            `line_kw`.

            .. versionadded:: 1.0

        contour_kw : dict, default=None
            Dict with keywords passed to the `matplotlib.pyplot.contourf`
            call for two-way partial dependence plots.

        bar_kw : dict, default=None
            Dict with keywords passed to the `matplotlib.pyplot.bar`
            call for one-way categorical partial dependence plots.

            .. versionadded:: 1.2

        heatmap_kw : dict, default=None
            Dict with keywords passed to the `matplotlib.pyplot.imshow`
            call for two-way categorical partial dependence plots.

            .. versionadded:: 1.2

        pdp_lim : dict, default=None
            Global min and max average predictions, such that all plots will have the
            same scale and y limits. `pdp_lim[1]` is the global min and max for single
            partial dependence curves. `pdp_lim[2]` is the global min and max for
            two-way partial dependence curves. If `None` (default), the limit will be
            inferred from the global minimum and maximum of all predictions.

            .. versionadded:: 1.1

        centered : bool, default=False
            If `True`, the ICE and PD lines will start at the origin of the
            y-axis. By default, no centering is done.

            .. versionadded:: 1.1

        Returns
        -------
        display : :class:`~sklearn.inspection.PartialDependenceDisplay`
            Returns a :class:`~sklearn.inspection.PartialDependenceDisplay`
            object that contains the partial dependence plots.
        """

        check_matplotlib_support("plot_partial_dependence")
        import matplotlib.pyplot as plt
        from matplotlib.gridspec import GridSpecFromSubplotSpec

        if isinstance(self.kind, str):
            kind = [self.kind] * len(self.features)
        else:
            kind = self.kind

        if self.is_categorical is None:
            is_categorical = [
                (False,) if len(fx) == 1 else (False, False) for fx in self.features
            ]
        else:
            is_categorical = self.is_categorical

        if len(kind) != len(self.features):
            raise ValueError(
                "When `kind` is provided as a list of strings, it should "
                "contain as many elements as `features`. `kind` contains "
                f"{len(kind)} element(s) and `features` contains "
                f"{len(self.features)} element(s)."
            )

        valid_kinds = {"average", "individual", "both"}
        if any([k not in valid_kinds for k in kind]):
            raise ValueError(
                f"Values provided to `kind` must be one of: {valid_kinds!r} or a list"
                f" of such values. Currently, kind={self.kind!r}"
            )

        # Center results before plotting
        if not centered:
            pd_results_ = self.pd_results
        else:
            pd_results_ = []
            for kind_plot, pd_result in zip(kind, self.pd_results):
                current_results = {"grid_values": pd_result["grid_values"]}

                if kind_plot in ("individual", "both"):
                    preds = pd_result.individual
                    preds = preds - preds[self.target_idx, :, 0, None]
                    current_results["individual"] = preds

                if kind_plot in ("average", "both"):
                    avg_preds = pd_result.average
                    avg_preds = avg_preds - avg_preds[self.target_idx, 0, None]
                    current_results["average"] = avg_preds

                pd_results_.append(Bunch(**current_results))

        if pdp_lim is None:
            # get global min and max average predictions of PD grouped by plot type
            pdp_lim = {}
            for kind_plot, pdp in zip(kind, pd_results_):
                values = pdp["grid_values"]
                preds = pdp.average if kind_plot == "average" else pdp.individual
                min_pd = preds[self.target_idx].min()
                max_pd = preds[self.target_idx].max()

                # expand the limits to account so that the plotted lines do not touch
                # the edges of the plot
                span = max_pd - min_pd
                min_pd -= 0.05 * span
                max_pd += 0.05 * span

                n_fx = len(values)
                old_min_pd, old_max_pd = pdp_lim.get(n_fx, (min_pd, max_pd))
                min_pd = min(min_pd, old_min_pd)
                max_pd = max(max_pd, old_max_pd)
                pdp_lim[n_fx] = (min_pd, max_pd)

        if line_kw is None:
            line_kw = {}
        if ice_lines_kw is None:
            ice_lines_kw = {}
        if pd_line_kw is None:
            pd_line_kw = {}
        if bar_kw is None:
            bar_kw = {}
        if heatmap_kw is None:
            heatmap_kw = {}

        if ax is None:
            _, ax = plt.subplots()

        if contour_kw is None:
            contour_kw = {}
        default_contour_kws = {"alpha": 0.75}
        contour_kw = _validate_style_kwargs(default_contour_kws, contour_kw)

        n_features = len(self.features)
        is_average_plot = [kind_plot == "average" for kind_plot in kind]
        if all(is_average_plot):
            # only average plots are requested
            n_ice_lines = 0
            n_lines = 1
        else:
            # we need to determine the number of ICE samples computed
            ice_plot_idx = is_average_plot.index(False)
            n_ice_lines = self._get_sample_count(
                len(pd_results_[ice_plot_idx].individual[0])
            )
            if any([kind_plot == "both" for kind_plot in kind]):
                n_lines = n_ice_lines + 1  # account for the average line
            else:
                n_lines = n_ice_lines

        if isinstance(ax, plt.Axes):
            # If ax was set off, it has most likely been set to off
            # by a previous call to plot.
            if not ax.axison:
                raise ValueError(
                    "The ax was already used in another plot "
                    "function, please set ax=display.axes_ "
                    "instead"
                )

            ax.set_axis_off()
            self.bounding_ax_ = ax
            self.figure_ = ax.figure

            n_cols = min(n_cols, n_features)
            n_rows = int(np.ceil(n_features / float(n_cols)))

            self.axes_ = np.empty((n_rows, n_cols), dtype=object)
            if all(is_average_plot):
                self.lines_ = np.empty((n_rows, n_cols), dtype=object)
            else:
                self.lines_ = np.empty((n_rows, n_cols, n_lines), dtype=object)
            self.contours_ = np.empty((n_rows, n_cols), dtype=object)
            self.bars_ = np.empty((n_rows, n_cols), dtype=object)
            self.heatmaps_ = np.empty((n_rows, n_cols), dtype=object)

            axes_ravel = self.axes_.ravel()

            gs = GridSpecFromSubplotSpec(
                n_rows, n_cols, subplot_spec=ax.get_subplotspec()
            )
            for i, spec in zip(range(n_features), gs):
                axes_ravel[i] = self.figure_.add_subplot(spec)

        else:  # array-like
            ax = np.asarray(ax, dtype=object)
            if ax.size != n_features:
                raise ValueError(
                    "Expected ax to have {} axes, got {}".format(n_features, ax.size)
                )

            if ax.ndim == 2:
                n_cols = ax.shape[1]
            else:
                n_cols = None

            self.bounding_ax_ = None
            self.figure_ = ax.ravel()[0].figure
            self.axes_ = ax
            if all(is_average_plot):
                self.lines_ = np.empty_like(ax, dtype=object)
            else:
                self.lines_ = np.empty(ax.shape + (n_lines,), dtype=object)
            self.contours_ = np.empty_like(ax, dtype=object)
            self.bars_ = np.empty_like(ax, dtype=object)
            self.heatmaps_ = np.empty_like(ax, dtype=object)

        # create contour levels for two-way plots
        if 2 in pdp_lim:
            Z_level = np.linspace(*pdp_lim[2], num=8)

        self.deciles_vlines_ = np.empty_like(self.axes_, dtype=object)
        self.deciles_hlines_ = np.empty_like(self.axes_, dtype=object)

        for pd_plot_idx, (axi, feature_idx, cat, pd_result, kind_plot) in enumerate(
            zip(
                self.axes_.ravel(),
                self.features,
                is_categorical,
                pd_results_,
                kind,
            )
        ):
            avg_preds = None
            preds = None
            feature_values = pd_result["grid_values"]
            if kind_plot == "individual":
                preds = pd_result.individual
            elif kind_plot == "average":
                avg_preds = pd_result.average
            else:  # kind_plot == 'both'
                avg_preds = pd_result.average
                preds = pd_result.individual

            if len(feature_values) == 1:
                # define the line-style for the current plot
                default_line_kws = {
                    "color": "C0",
                    "label": "average" if kind_plot == "both" else None,
                }
                if kind_plot == "individual":
                    default_ice_lines_kws = {"alpha": 0.3, "linewidth": 0.5}
                    default_pd_lines_kws = {}
                elif kind_plot == "both":
                    # by default, we need to distinguish the average line from
                    # the individual lines via color and line style
                    default_ice_lines_kws = {
                        "alpha": 0.3,
                        "linewidth": 0.5,
                        "color": "tab:blue",
                    }
                    default_pd_lines_kws = {
                        "color": "tab:orange",
                        "linestyle": "--",
                    }
                else:
                    default_ice_lines_kws = {}
                    default_pd_lines_kws = {}

                default_ice_lines_kws = {**default_line_kws, **default_ice_lines_kws}
                default_pd_lines_kws = {**default_line_kws, **default_pd_lines_kws}

                line_kw = _validate_style_kwargs(default_line_kws, line_kw)

                ice_lines_kw = _validate_style_kwargs(
                    _validate_style_kwargs(default_ice_lines_kws, line_kw), ice_lines_kw
                )
                del ice_lines_kw["label"]

                pd_line_kw = _validate_style_kwargs(
                    _validate_style_kwargs(default_pd_lines_kws, line_kw), pd_line_kw
                )

                default_bar_kws = {"color": "C0"}
                bar_kw = _validate_style_kwargs(default_bar_kws, bar_kw)

                default_heatmap_kw = {}
                heatmap_kw = _validate_style_kwargs(default_heatmap_kw, heatmap_kw)

                self._plot_one_way_partial_dependence(
                    kind_plot,
                    preds,
                    avg_preds,
                    feature_values[0],
                    feature_idx,
                    n_ice_lines,
                    axi,
                    n_cols,
                    pd_plot_idx,
                    n_lines,
                    ice_lines_kw,
                    pd_line_kw,
                    cat[0],
                    bar_kw,
                    pdp_lim,
                )
            else:
                self._plot_two_way_partial_dependence(
                    avg_preds,
                    feature_values,
                    feature_idx,
                    axi,
                    pd_plot_idx,
                    Z_level,
                    contour_kw,
                    cat[0] and cat[1],
                    heatmap_kw,
                )

        return self