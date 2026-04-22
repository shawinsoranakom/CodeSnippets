def is_pandas_version_less_than(v: str) -> bool:
    """Return True if the current Pandas version is less than the input version.

    Parameters
    ----------
    v : str
        Version string, e.g. "0.25.0"

    Returns
    -------
    bool

    """
    import pandas as pd
    from packaging import version

    return version.parse(pd.__version__) < version.parse(v)