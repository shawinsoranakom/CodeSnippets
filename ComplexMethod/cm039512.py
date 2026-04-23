def _check_figure_axes_and_labels(display, pos_label):
    """Check mpl axes and figure defaults are correct."""
    import matplotlib as mpl

    assert isinstance(display.ax_, mpl.axes.Axes)
    assert isinstance(display.figure_, mpl.figure.Figure)
    assert display.ax_.get_adjustable() == "box"
    assert display.ax_.get_aspect() in ("equal", 1.0)
    assert display.ax_.get_xlim() == display.ax_.get_ylim() == (-0.01, 1.01)

    expected_pos_label = 1 if pos_label is None else pos_label
    expected_ylabel = f"True Positive Rate (Positive label: {expected_pos_label})"
    expected_xlabel = f"False Positive Rate (Positive label: {expected_pos_label})"

    assert display.ax_.get_ylabel() == expected_ylabel
    assert display.ax_.get_xlabel() == expected_xlabel