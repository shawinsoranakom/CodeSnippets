def from_estimator(
        cls,
        estimator,
        X,
        *,
        grid_resolution=100,
        eps=1.0,
        plot_method="contourf",
        response_method="auto",
        class_of_interest=None,
        multiclass_colors=None,
        xlabel=None,
        ylabel=None,
        ax=None,
        **kwargs,
    ):
        """Plot decision boundary given an estimator.

        Read more in the :ref:`User Guide <visualizations>`.

        Parameters
        ----------
        estimator : object
            Trained estimator used to plot the decision boundary.

        X : {array-like, sparse matrix, dataframe} of shape (n_samples, 2)
            Input data that should be only 2-dimensional.

        grid_resolution : int, default=100
            Number of grid points to use for plotting decision boundary.
            Higher values will make the plot look nicer but be slower to
            render.

        eps : float, default=1.0
            Extends the minimum and maximum values of X for evaluating the
            response function.

        plot_method : {'contourf', 'contour', 'pcolormesh'}, default='contourf'
            Plotting method to call when plotting the response. Please refer
            to the following matplotlib documentation for details:
            :func:`contourf <matplotlib.pyplot.contourf>`,
            :func:`contour <matplotlib.pyplot.contour>`,
            :func:`pcolormesh <matplotlib.pyplot.pcolormesh>`.

        response_method : {'auto', 'decision_function', 'predict_proba', \
                'predict'}, default='auto'
            Specifies whether to use :term:`decision_function`,
            :term:`predict_proba` or :term:`predict` as the target response.
            If set to 'auto', the response method is tried in the order as
            listed above.

            .. versionchanged:: 1.6
                For multiclass problems, 'auto' no longer defaults to 'predict'.

        class_of_interest : int, float, bool or str, default=None
            The class to be plotted. For :term:`binary` classifiers, if None,
            `estimator.classes_[1]` is considered the positive class. For
            :term:`multiclass` classifiers, if None, all classes will be represented in
            the decision boundary plot; when `response_method` is :term:`predict_proba`
            or :term:`decision_function`, the class with the highest response value
            at each point is plotted. The color of each class can be set via
            `multiclass_colors`.

            .. versionadded:: 1.4

        multiclass_colors : str or list of matplotlib colors, default=None
            Specifies how to color each class when plotting :term:`multiclass` problems
            and `class_of_interest` is None.

            Possible inputs are:

            * None: defaults to list of accessible `Petroff colors
              <https://github.com/matplotlib/matplotlib/issues/9460#issuecomment-875185352>`_
              if `n_classes <= 10`, otherwise 'gist_rainbow' colormap
            * str: name of :class:`matplotlib.colors.Colormap`
            * list: list of length `n_classes` of `matplotlib colors
              <https://matplotlib.org/stable/users/explain/colors/colors.html#colors-def>`_

            Single color (fading to white) colormaps will be generated from the colors
            in the list or colors taken from the colormap, and passed to the `cmap`
            parameter of the `plot_method`.

            When `response_method='predict'` and `plot_method='contour'`,
            `multiclass_colors` is ignored and the class boundaries are plotted in black
            instead as the boundary lines may overlap and the colors don't necessarily
            correspond to the classes.

            For :term:`binary` problems, `multiclass_colors` is also ignored and `cmap`
            or `colors` can be passed as kwargs instead, otherwise, the default colormap
            ('viridis') is used.

            .. versionadded:: 1.7
            .. versionchanged:: 1.9
                `multiclass_colors` is now also used when `response_method="predict"`,
                except for when `plot_method='contour'`, where it is ignored and "black"
                is used instead.
                The default colors changed from 'tab10' to the more accessible `Petroff
                colors <https://github.com/matplotlib/matplotlib/issues/9460#issuecomment-875185352>`_.

        xlabel : str, default=None
            The label used for the x-axis. If `None`, an attempt is made to
            extract a label from `X` if it is a dataframe, otherwise an empty
            string is used.

        ylabel : str, default=None
            The label used for the y-axis. If `None`, an attempt is made to
            extract a label from `X` if it is a dataframe, otherwise an empty
            string is used.

        ax : Matplotlib axes, default=None
            Axes object to plot on. If `None`, a new figure and axes is
            created.

        **kwargs : dict
            Additional keyword arguments to be passed to the `plot_method`.

        Returns
        -------
        display : :class:`~sklearn.inspection.DecisionBoundaryDisplay`
            Object that stores the result.

        See Also
        --------
        DecisionBoundaryDisplay : Decision boundary visualization.
        sklearn.metrics.ConfusionMatrixDisplay.from_estimator : Plot the
            confusion matrix given an estimator, the data, and the label.
        sklearn.metrics.ConfusionMatrixDisplay.from_predictions : Plot the
            confusion matrix given the true and predicted labels.

        Examples
        --------
        >>> import matplotlib as mpl
        >>> import matplotlib.pyplot as plt
        >>> from sklearn.datasets import load_iris
        >>> from sklearn.linear_model import LogisticRegression
        >>> from sklearn.inspection import DecisionBoundaryDisplay
        >>> iris = load_iris()
        >>> X = iris.data[:, :2]
        >>> classifier = LogisticRegression().fit(X, iris.target)
        >>> disp = DecisionBoundaryDisplay.from_estimator(
        ...     classifier, X, response_method="predict",
        ...     xlabel=iris.feature_names[0], ylabel=iris.feature_names[1],
        ...     alpha=0.5,
        ... )
        >>> cmap = mpl.colors.ListedColormap(disp.multiclass_colors_)
        >>> disp.ax_.scatter(X[:, 0], X[:, 1], c=iris.target, edgecolor="k", cmap=cmap)
        <...>
        >>> plt.show()
        """
        check_is_fitted(estimator)

        if not grid_resolution > 1:
            raise ValueError(
                "grid_resolution must be greater than 1. Got"
                f" {grid_resolution} instead."
            )

        if not eps >= 0:
            raise ValueError(
                f"eps must be greater than or equal to 0. Got {eps} instead."
            )

        possible_plot_methods = ("contourf", "contour", "pcolormesh")
        if plot_method not in possible_plot_methods:
            available_methods = ", ".join(possible_plot_methods)
            raise ValueError(
                f"plot_method must be one of {available_methods}. "
                f"Got {plot_method} instead."
            )

        num_features = _num_features(X)
        if num_features != 2:
            raise ValueError(
                f"n_features must be equal to 2. Got {num_features} instead."
            )

        x0, x1 = _safe_indexing(X, 0, axis=1), _safe_indexing(X, 1, axis=1)

        x0_min, x0_max = x0.min() - eps, x0.max() + eps
        x1_min, x1_max = x1.min() - eps, x1.max() + eps

        xx0, xx1 = np.meshgrid(
            np.linspace(x0_min, x0_max, grid_resolution),
            np.linspace(x1_min, x1_max, grid_resolution),
        )

        X_grid = np.c_[xx0.ravel(), xx1.ravel()]
        if is_pandas_df(X) or is_polars_df(X):
            adapter = _get_adapter_from_container(X)
            X_grid = adapter.create_container(
                X_grid,
                X_grid,
                columns=X.columns,
            )

        prediction_method = _check_boundary_response_method(estimator, response_method)
        if (class_of_interest is not None and hasattr(estimator, "classes_")) and (
            class_of_interest not in estimator.classes_
        ):
            raise ValueError(
                f"class_of_interest={class_of_interest} is not a valid label: It "
                f"should be one of {estimator.classes_}"
            )

        response, _, response_method_used = _get_response_values(
            estimator,
            X_grid,
            response_method=prediction_method,
            pos_label=class_of_interest,
            return_response_method_used=True,
        )

        # convert classes predictions into integers
        if response_method_used == "predict" and hasattr(estimator, "classes_"):
            encoder = LabelEncoder()
            encoder.classes_ = estimator.classes_
            response = encoder.transform(response)

        # infer n_classes from the estimator
        if (
            class_of_interest is not None
            or is_regressor(estimator)
            or is_outlier_detector(estimator)
        ):
            n_classes = 2
        elif is_classifier(estimator) and hasattr(estimator, "classes_"):
            n_classes = len(estimator.classes_)
        elif is_clusterer(estimator) and hasattr(estimator, "labels_"):
            n_classes = len(np.unique(estimator.labels_))
        else:
            target_type = type_of_target(response)
            if target_type in ("binary", "continuous"):
                n_classes = 2
            elif target_type == "multiclass":
                n_classes = len(np.unique(response))
            else:
                raise ValueError(
                    "Number of classes or labels cannot be inferred from "
                    f"{estimator.__class__.__name__}. Please make sure your estimator "
                    "follows scikit-learn's estimator API as described here: "
                    "https://scikit-learn.org/stable/developers/develop.html#rolling-your-own-estimator"
                )

        if response.ndim == 1:
            response = response.reshape(*xx0.shape)
        else:
            if is_regressor(estimator):
                raise ValueError("Multi-output regressors are not supported")

            if class_of_interest is not None:
                # For the multiclass case, `_get_response_values` returns the response
                # as-is. Thus, we have a column per class and we need to select the
                # column corresponding to the positive class.
                col_idx = np.flatnonzero(estimator.classes_ == class_of_interest)[0]
                response = response[:, col_idx].reshape(*xx0.shape)
            else:
                response = response.reshape(*xx0.shape, response.shape[-1])

        if xlabel is None:
            xlabel = X.columns[0] if hasattr(X, "columns") else ""

        if ylabel is None:
            ylabel = X.columns[1] if hasattr(X, "columns") else ""

        display = cls(
            xx0=xx0,
            xx1=xx1,
            n_classes=n_classes,
            response=response,
            multiclass_colors=multiclass_colors,
            xlabel=xlabel,
            ylabel=ylabel,
        )
        return display.plot(ax=ax, plot_method=plot_method, **kwargs)