def _select_colors(mpl, multiclass_colors, n_classes):
    """Select colors for multiclass decision boundary display.

    Parameters
    ----------
    mpl : module
        Imported `matplotlib` module.

    multiclass_colors : str or list of matplotlib colors, default=None
        The colormap or colors to select.

        Possible inputs are:

        * None: defaults to list of accessible `Petroff colors
          <https://github.com/matplotlib/matplotlib/issues/9460#issuecomment-875185352>`_
          if `n_classes <= 10`, otherwise 'gist_rainbow' colormap
        * str: name of :class:`matplotlib.colors.Colormap`
        * list: list of length `n_classes` of `matplotlib colors
          <https://matplotlib.org/stable/users/explain/colors/colors.html#colors-def>`_

    n_classes : int
        Number of colors to select.

    Returns
    -------
    colors : ndarray of shape (n_classes, 4)
        RGBA colors, one per class.

    """

    if multiclass_colors is None:
        # select accessible colors according to Matthew A. Petroff, see
        # https://arxiv.org/abs/2107.02270 and
        # https://github.com/matplotlib/matplotlib/issues/9460#issuecomment-875185352
        if n_classes <= 10:
            multiclass_colors = PETROFF_COLORS[:n_classes]
        else:
            multiclass_colors = "gist_rainbow"

    if isinstance(multiclass_colors, str):
        if multiclass_colors not in mpl.pyplot.colormaps():
            raise ValueError(
                "When 'multiclass_colors' is a string, it must be a valid "
                f"Matplotlib colormap. Got: {multiclass_colors}"
            )
        cmap = mpl.pyplot.get_cmap(multiclass_colors)
        if cmap.N < n_classes:
            raise ValueError(
                f"Colormap '{multiclass_colors}' only has {cmap.N} colors, but "
                f"{n_classes} classes are to be displayed. Please specify a "
                "different colormap or provide a list of colors via "
                "'multiclass_colors'."
            )
        return cmap(np.linspace(0, 1, n_classes))

    elif isinstance(multiclass_colors, list):
        if len(multiclass_colors) != n_classes:
            raise ValueError(
                "When 'multiclass_colors' is a list, it must be of the same "
                f"length as the classes or labels to plot ({n_classes}), got: "
                f"{len(multiclass_colors)}."
            )
        elif any(not mpl.colors.is_color_like(col) for col in multiclass_colors):
            raise ValueError(
                "When 'multiclass_colors' is a list, it can only contain valid"
                f" Matplotlib color names. Got: {multiclass_colors}"
            )
        return mpl.colors.to_rgba_array(multiclass_colors)

    else:
        raise TypeError("'multiclass_colors' must be a list or a str.")