def _validate_curve_kwargs(
        n_curves,
        name,
        legend_metric,
        legend_metric_name,
        curve_kwargs,
        default_curve_kwargs=None,
        default_multi_curve_kwargs=None,
        removed_version="1.9",
        **kwargs,
    ):
        """Get validated line kwargs for each curve.

        Parameters
        ----------
        n_curves : int
            Number of curves.

        name : list of str or None
            Name for labeling legend entries.

        legend_metric : dict
            Dictionary with "mean" and "std" keys, or "metric" key of metric
            values for each curve. If None, "label" will not contain metric values.

        legend_metric_name : str
            Name of the summary value provided in `legend_metrics`.

        curve_kwargs : dict or list of dict or None
            Dictionary with keywords passed to the matplotlib's `plot` function
            to draw the individual curves. If a list is provided, the
            parameters are applied to the curves sequentially. If a single
            dictionary is provided, the same parameters are applied to all
            curves.

        default_curve_kwargs : dict, default=None
            Default curve kwargs, to be added to all curves. Individual kwargs
            are over-ridden by `curve_kwargs`, if kwarg also set in `curve_kwargs`.

        default_multi_curve_kwargs : dict, default=None
            Default curve kwargs for multi-curve plots. Individual kwargs
            are over-ridden by `curve_kwargs`, if kwarg also set in `curve_kwargs`.

        removed_version : str, default="1.9"
            Version in which `kwargs` will be removed.

        **kwargs : dict
            Deprecated. Keyword arguments to be passed to matplotlib's `plot`.
        """
        # TODO: Remove once kwargs deprecated on all displays
        if curve_kwargs and kwargs:
            raise ValueError(
                "Cannot provide both `curve_kwargs` and `kwargs`. `**kwargs` is "
                f"deprecated and will be removed in {removed_version}. Pass all "
                "matplotlib arguments to `curve_kwargs` as a dictionary."
            )
        if kwargs:
            warnings.warn(
                f"`**kwargs` is deprecated and will be removed in {removed_version}. "
                "Pass all matplotlib arguments to `curve_kwargs` as a dictionary "
                "instead.",
                FutureWarning,
            )
            curve_kwargs = kwargs

        if isinstance(curve_kwargs, list) and len(curve_kwargs) != n_curves:
            raise ValueError(
                f"`curve_kwargs` must be None, a dictionary or a list of length "
                f"{n_curves}. Got: {curve_kwargs}."
            )

        # Ensure valid `name` and `curve_kwargs` combination.
        if (
            isinstance(name, list)
            and len(name) != 1
            and not isinstance(curve_kwargs, list)
        ):
            raise ValueError(
                "To avoid labeling individual curves that have the same appearance, "
                f"`curve_kwargs` should be a list of {n_curves} dictionaries. "
                "Alternatively, set `name` to `None` or a single string to label "
                "a single legend entry for all curves."
            )

        # Ensure `name` is of the correct length
        if isinstance(name, str):
            name = [name]
        if isinstance(name, list) and len(name) == 1:
            name = name * n_curves
        name = [None] * n_curves if name is None else name

        # Ensure `curve_kwargs` is of correct length
        if isinstance(curve_kwargs, Mapping):
            curve_kwargs = [curve_kwargs] * n_curves
        elif curve_kwargs is None:
            curve_kwargs = [{}] * n_curves

        if default_curve_kwargs is None:
            default_curve_kwargs = {}
        if default_multi_curve_kwargs is None:
            default_multi_curve_kwargs = {}

        if n_curves > 1:
            default_curve_kwargs.update(default_multi_curve_kwargs)

        labels = []
        if "mean" in legend_metric:
            label_aggregate = _BinaryClassifierCurveDisplayMixin._get_legend_label(
                legend_metric["mean"], name[0], legend_metric_name
            )
            # Note: "std" always `None` when "mean" is `None` - no metric value added
            # to label in this case
            if legend_metric["std"] is not None:
                # Add the "+/- std" to the end (in brackets if name provided)
                if name[0] is not None:
                    label_aggregate = (
                        label_aggregate[:-1] + f" +/- {legend_metric['std']:0.2f})"
                    )
                else:
                    label_aggregate = (
                        label_aggregate + f" +/- {legend_metric['std']:0.2f}"
                    )
            # Add `label` for first curve only, set to `None` for remaining curves
            labels.extend([label_aggregate] + [None] * (n_curves - 1))
        else:
            for curve_legend_metric, curve_name in zip(legend_metric["metric"], name):
                labels.append(
                    _BinaryClassifierCurveDisplayMixin._get_legend_label(
                        curve_legend_metric, curve_name, legend_metric_name
                    )
                )

        curve_kwargs_ = [
            _validate_style_kwargs(
                {"label": label, **default_curve_kwargs}, curve_kwargs[fold_idx]
            )
            for fold_idx, label in enumerate(labels)
        ]
        return curve_kwargs_