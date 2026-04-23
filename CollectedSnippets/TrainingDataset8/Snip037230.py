def _trim_pandas_styles(styles):
    """Trim pandas styles dict.

    Parameters
    ----------
    styles : dict
        pandas.Styler translated styles.

    """
    # Filter out empty styles, as every cell will have a class
    # but the list of props may just be [['', '']].
    return [x for x in styles if any(any(y) for y in x["props"])]