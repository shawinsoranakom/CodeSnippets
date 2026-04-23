def plot(
        self,
        ax=None,
        *,
        name=None,
        curve_kwargs=None,
        plot_chance_level=False,
        chance_level_kw=None,
        despine=False,
        **kwargs,
    ):
        """Plot visualization.

        Parameters
        ----------
        ax : Matplotlib Axes, default=None
            Axes object to plot on. If `None`, a new figure and axes is
            created.

        name : str or list of str, default=None
            Name for labeling legend entries. The number of legend entries
            is determined by `curve_kwargs`, and is not affected by `name`.

            If a string is provided, it will be used to either label the single legend
            entry or if there are multiple legend entries, label each individual curve
            with the same name.

            If a list is provided, it will be used to label each curve individually.
            Passing a list will raise an error if `curve_kwargs` is not a list to avoid
            labeling individual curves that have the same appearance.

            If `None`, set to `name` provided at `PrecisionRecallDisplay`
            initialization. If still `None`, no name is shown in the legend.

            .. versionchanged:: 1.9
                Now accepts a list for plotting multiple curves.

        curve_kwargs : dict or list of dict, default=None
            Keywords arguments to be passed to matplotlib's `plot` function
            to draw individual precision-recall curves. For single curve plotting, this
            should be a dictionary. For multi-curve plotting, if a list is provided,
            the parameters are applied to each precision-recall curve
            sequentially and a legend entry is added for each curve.
            If a single dictionary is provided, the same parameters are applied
            to all curves and a single legend entry for all curves is added,
            labeled with the mean average precision.

            .. versionadded:: 1.9

        plot_chance_level : bool, default=False
            Whether to plot the chance level. The chance level is the prevalence
            of the positive label computed from the data passed during
            :meth:`from_estimator` or :meth:`from_predictions` call.

            .. versionadded:: 1.3

        chance_level_kw : dict, default=None
            Keyword arguments to be passed to matplotlib's `plot` for rendering
            the chance level line.

            .. versionadded:: 1.3

        despine : bool, default=False
            Whether to remove the top and right spines from the plot.

            .. versionadded:: 1.6

        **kwargs : dict
            Keyword arguments to be passed to matplotlib's `plot`.

            .. deprecated:: 1.9
                kwargs is deprecated and will be removed in 1.11. Pass matplotlib
                arguments to `curve_kwargs` as a dictionary instead.

        Returns
        -------
        display : :class:`~sklearn.metrics.PrecisionRecallDisplay`
            Object that stores computed values.

        Notes
        -----
        The average precision (cf. :func:`~sklearn.metrics.average_precision_score`)
        in scikit-learn is computed without any interpolation. To be consistent
        with this metric, the precision-recall curve is plotted without any
        interpolation as well (step-wise style).

        To enable interpolation, pass `curve_kwargs={"drawstyle": "default"}`.
        However, the curve will not be strictly consistent with the reported
        average precision.
        """
        precision, recall, average_precision, name, prevalence_pos_label = (
            self._validate_plot_params(ax=ax, name=name)
        )
        n_curves = len(precision)
        average_precision, legend_metric = self._get_legend_metric(
            curve_kwargs, n_curves, average_precision
        )

        curve_kwargs = self._validate_curve_kwargs(
            n_curves,
            name,
            legend_metric,
            "AP",
            curve_kwargs=curve_kwargs,
            default_curve_kwargs={"drawstyle": "steps-post"},
            default_multi_curve_kwargs={
                "alpha": 0.5,
                "linestyle": "--",
                "color": "blue",
            },
            removed_version="1.11",
            **kwargs,
        )
        self.line_ = []
        for recall_val, precision_val, curve_kwarg in zip(
            recall, precision, curve_kwargs
        ):
            self.line_.extend(self.ax_.plot(recall_val, precision_val, **curve_kwarg))
        # Return single artist if only one curve is plotted
        if len(self.line_) == 1:
            self.line_ = self.line_[0]

        info_pos_label = (
            f" (Positive label: {self.pos_label})" if self.pos_label is not None else ""
        )

        xlabel = "Recall" + info_pos_label
        ylabel = "Precision" + info_pos_label
        self.ax_.set(
            xlabel=xlabel,
            xlim=(-0.01, 1.01),
            ylabel=ylabel,
            ylim=(-0.01, 1.01),
            aspect="equal",
        )

        if plot_chance_level:
            if self.prevalence_pos_label is None:
                raise ValueError(
                    "You must provide prevalence_pos_label when constructing the "
                    "PrecisionRecallDisplay object in order to plot the chance "
                    "level line. Alternatively, you may use "
                    "PrecisionRecallDisplay.from_estimator or "
                    "PrecisionRecallDisplay.from_predictions "
                    "to automatically set prevalence_pos_label"
                )

            default_chance_level_kwargs = {
                "color": "k",
                "linestyle": "--",
            }
            if n_curves > 1:
                default_chance_level_kwargs["alpha"] = 0.3

            if chance_level_kw is None:
                chance_level_kw = {}

            chance_level_kw = _validate_style_kwargs(
                default_chance_level_kwargs, chance_level_kw
            )
            self.chance_level_ = []
            for prevalence in prevalence_pos_label:
                self.chance_level_.extend(
                    self.ax_.plot(
                        (0, 1),
                        (prevalence, prevalence),
                        **chance_level_kw,
                    )
                )

            if "label" not in chance_level_kw:
                label = (
                    f"Chance level (AP = {prevalence_pos_label[0]:0.2f})"
                    if n_curves == 1
                    else f"Chance level (AP = {np.mean(prevalence_pos_label):0.2f} "
                    f"+/- {np.std(prevalence_pos_label):0.2f})"
                )
                # Only label first curve with mean AP, to get single legend entry
                self.chance_level_[0].set_label(label)

            if n_curves == 1:
                # Return single artist if only one curve is plotted
                self.chance_level_ = self.chance_level_[0]
        else:
            self.chance_level_ = None

        if despine:
            _despine(self.ax_)

        # Note: if 'label' present in one `line_kwargs`, it should be present in all
        if curve_kwargs[0].get("label") is not None or (
            plot_chance_level and chance_level_kw.get("label") is not None
        ):
            self.ax_.legend(loc="lower left")

        return self