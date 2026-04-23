def plot(self, plot_method="contourf", ax=None, xlabel=None, ylabel=None, **kwargs):
        """Plot visualization.

        Parameters
        ----------
        plot_method : {'contourf', 'contour', 'pcolormesh'}, default='contourf'
            Plotting method to call when plotting the response. Please refer
            to the following matplotlib documentation for details:
            :func:`contourf <matplotlib.pyplot.contourf>`,
            :func:`contour <matplotlib.pyplot.contour>`,
            :func:`pcolormesh <matplotlib.pyplot.pcolormesh>`.

        ax : Matplotlib axes, default=None
            Axes object to plot on. If `None`, a new figure and axes is
            created.

        xlabel : str, default=None
            Overwrite the x-axis label.

        ylabel : str, default=None
            Overwrite the y-axis label.

        **kwargs : dict
            Additional keyword arguments to be passed to the `plot_method`. For
            :term:`binary` problems, `cmap` or `colors` can be set here to specify the
            colormap or colors, otherwise the default colormap ('viridis') is used. If
            not specified by the user, `zorder` is set to -1 to ensure that the decision
            boundary is plotted in the background (in case a scatter plot is added on
            top).

        Returns
        -------
        display: :class:`~sklearn.inspection.DecisionBoundaryDisplay`
            Object that stores computed values.
        """
        check_matplotlib_support("DecisionBoundaryDisplay.plot")
        import matplotlib as mpl
        import matplotlib.pyplot as plt

        if plot_method not in ("contourf", "contour", "pcolormesh"):
            raise ValueError(
                "plot_method must be 'contourf', 'contour', or 'pcolormesh'. "
                f"Got {plot_method} instead."
            )

        if ax is None:
            _, ax = plt.subplots()

        plot_func = getattr(ax, plot_method)
        if self.n_classes == 2:
            self.surface_ = plot_func(self.xx0, self.xx1, self.response, **kwargs)
        else:  # multiclass
            for kwarg in ("cmap", "colors"):
                if kwarg in kwargs:
                    warnings.warn(
                        f"'{kwarg}' is ignored in favor of 'multiclass_colors' "
                        "in the multiclass case."
                    )
                    del kwargs[kwarg]

            self.multiclass_colors_ = _select_colors(
                mpl, self.multiclass_colors, self.n_classes
            )

            # If not set by the user, set default values for `zorder` to ensure that the
            # decision boundary is plotted in the background (in case a scatter plot is
            # added on top)
            if "zorder" not in kwargs:
                kwargs["zorder"] = -1

            if self.response.ndim == 3:  # predict_proba and decision_function
                multiclass_cmaps = [
                    mpl.colors.LinearSegmentedColormap.from_list(
                        f"colormap_{class_idx}",
                        [(1.0, 1.0, 1.0, 1.0), (r, g, b, 1.0)],
                    )
                    for class_idx, (r, g, b, _) in enumerate(self.multiclass_colors_)
                ]
                self.surface_ = []
                for class_idx, cmap in enumerate(multiclass_cmaps):
                    response = np.ma.array(
                        self.response[:, :, class_idx],
                        mask=(self.response.argmax(axis=2) != class_idx),
                    )
                    self.surface_.append(
                        plot_func(self.xx0, self.xx1, response, cmap=cmap, **kwargs)
                    )

                if plot_method == "contour":
                    # Additionally plot the decision boundaries between classes.
                    self.surface_.append(
                        plot_func(
                            self.xx0,
                            self.xx1,
                            self.response.argmax(axis=2),
                            colors="black",
                            zorder=-1,
                            # set levels to ensure all boundaries are plotted correctly
                            levels=np.arange(self.n_classes),
                        )
                    )

            elif self.response.ndim == 2:  # predict
                # Set `levels` to ensure all class boundaries are displayed.
                if "levels" not in kwargs:
                    if plot_method == "contour":
                        kwargs["levels"] = np.arange(self.n_classes)
                    elif plot_method == "contourf":
                        kwargs["levels"] = np.arange(self.n_classes + 1) - 0.5

                if plot_method == "contour":
                    self.surface_ = plot_func(
                        self.xx0, self.xx1, self.response, colors="black", **kwargs
                    )
                else:
                    # `pcolormesh` requires cmap, for `contourf` it makes no difference
                    cmap = mpl.colors.ListedColormap(self.multiclass_colors_)
                    self.surface_ = plot_func(
                        self.xx0, self.xx1, self.response, cmap=cmap, **kwargs
                    )

        if xlabel is not None or not ax.get_xlabel():
            xlabel = self.xlabel if xlabel is None else xlabel
            ax.set_xlabel(xlabel)
        if ylabel is not None or not ax.get_ylabel():
            ylabel = self.ylabel if ylabel is None else ylabel
            ax.set_ylabel(ylabel)

        self.ax_ = ax
        self.figure_ = ax.figure
        return self