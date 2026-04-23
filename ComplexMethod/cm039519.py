def _check_figure_axes_and_labels(display, pos_label):
    """Check mpl figure and axes are correct."""
    import matplotlib as mpl

    assert isinstance(display.ax_, mpl.axes.Axes)
    assert isinstance(display.figure_, mpl.figure.Figure)

    assert display.ax_.get_xlabel() == f"Recall (Positive label: {pos_label})"
    assert display.ax_.get_ylabel() == f"Precision (Positive label: {pos_label})"
    assert display.ax_.get_adjustable() == "box"
    assert display.ax_.get_aspect() in ("equal", 1.0)
    assert display.ax_.get_xlim() == display.ax_.get_ylim() == (-0.01, 1.01)