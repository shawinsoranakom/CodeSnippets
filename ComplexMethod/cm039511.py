def plot(
        self,
        ax=None,
        *,
        name=None,
        curve_kwargs=None,
        plot_chance_level=False,
        chance_level_kw=None,
        despine=False,
    ):
        """Plot visualization.

        Parameters
        ----------
        ax : matplotlib axes, default=None
            Axes object to plot on. If `None`, a new figure and axes is
            created.

        name : str or list of str, default=None
            Name for labeling legend entries. The number of legend entries is determined
            by the `curve_kwargs` passed to `plot`, and is not affected by `name`.

            If a string is provided, it will be used to either label the single legend
            entry or if there are multiple legend entries, label each individual curve
            with the same name.

            If a list is provided, it will be used to label each curve individually.
            Passing a list will raise an error if `curve_kwargs` is not a list to avoid
            labeling individual curves that have the same appearance.

            If `None`, set to `name` provided at `RocCurveDisplay` initialization. If
            still `None`, no name is shown in the legend.

            .. versionadded:: 1.7

        curve_kwargs : dict or list of dict, default=None
            Keywords arguments to be passed to matplotlib's `plot` function
            to draw individual ROC curves. For single curve plotting, should be
            a dictionary. For multi-curve plotting, if a list is provided the
            parameters are applied to the ROC curves of each CV fold
            sequentially and a legend entry is added for each curve.
            If a single dictionary is provided, the same parameters are applied
            to all ROC curves and a single legend entry for all curves is added,
            labeled with the mean ROC AUC score.

            .. versionadded:: 1.7

        plot_chance_level : bool, default=False
            Whether to plot the chance level.

            .. versionadded:: 1.3

        chance_level_kw : dict, default=None
            Keyword arguments to be passed to matplotlib's `plot` for rendering
            the chance level line.

            .. versionadded:: 1.3

        despine : bool, default=False
            Whether to remove the top and right spines from the plot.

            .. versionadded:: 1.6

        Returns
        -------
        display : :class:`~sklearn.metrics.RocCurveDisplay`
            Object that stores computed values.
        """
        fpr, tpr, roc_auc, name = self._validate_plot_params(ax=ax, name=name)
        n_curves = len(fpr)
        roc_auc, legend_metric = self._get_legend_metric(
            curve_kwargs, n_curves, roc_auc
        )

        curve_kwargs = self._validate_curve_kwargs(
            n_curves,
            name,
            legend_metric,
            "AUC",
            curve_kwargs=curve_kwargs,
            default_multi_curve_kwargs={
                "alpha": 0.5,
                "linestyle": "--",
                "color": "blue",
            },
        )

        default_chance_level_line_kw = {
            "label": "Chance level (AUC = 0.5)",
            "color": "k",
            "linestyle": "--",
        }

        if chance_level_kw is None:
            chance_level_kw = {}

        chance_level_kw = _validate_style_kwargs(
            default_chance_level_line_kw, chance_level_kw
        )

        self.line_ = []
        for fpr, tpr, line_kw in zip(fpr, tpr, curve_kwargs):
            self.line_.extend(self.ax_.plot(fpr, tpr, **line_kw))
        # Return single artist if only one curve is plotted
        if len(self.line_) == 1:
            self.line_ = self.line_[0]

        info_pos_label = (
            f" (Positive label: {self.pos_label})" if self.pos_label is not None else ""
        )

        xlabel = "False Positive Rate" + info_pos_label
        ylabel = "True Positive Rate" + info_pos_label
        self.ax_.set(
            xlabel=xlabel,
            xlim=(-0.01, 1.01),
            ylabel=ylabel,
            ylim=(-0.01, 1.01),
            aspect="equal",
        )

        if plot_chance_level:
            (self.chance_level_,) = self.ax_.plot((0, 1), (0, 1), **chance_level_kw)
        else:
            self.chance_level_ = None

        if despine:
            _despine(self.ax_)

        if curve_kwargs[0].get("label") is not None or (
            plot_chance_level and chance_level_kw.get("label") is not None
        ):
            self.ax_.legend(loc="lower right")

        return self