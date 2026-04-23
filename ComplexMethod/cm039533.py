def test_display_validate_plot_params(pyplot, Display, display_args):
    """Check `_validate_plot_params` returns the correct variables.

    `display_args` should be given in the same order as output by
    `_validate_plot_params`. All `display_args` should be for a single curve.
    """
    display = Display(**display_args)
    results = display._validate_plot_params(ax=None, name=None)

    # Check if the number of parameters match
    assert len(results) == len(display_args)

    for idx, (param, value) in enumerate(display_args.items()):
        if param == "name":
            assert results[idx] == [value] if isinstance(value, str) else value
        elif value is None:
            assert results[idx] is None
        else:
            assert isinstance(results[idx], list)
            assert len(results[idx]) == 1