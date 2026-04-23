def _pandas_dtype_needs_early_conversion(pd_dtype):
    """Return True if pandas extension pd_dtype need to be converted early."""
    # Check these early for pandas versions without extension dtypes
    from pandas import SparseDtype
    from pandas.api.types import (
        is_bool_dtype,
        is_float_dtype,
        is_integer_dtype,
    )

    if is_bool_dtype(pd_dtype):
        # bool and extension booleans need early conversion because __array__
        # converts mixed dtype dataframes into object dtypes
        return True

    if isinstance(pd_dtype, SparseDtype):
        # Sparse arrays will be converted later in `check_array`
        return False

    try:
        from pandas.api.types import is_extension_array_dtype
    except ImportError:
        return False

    if isinstance(pd_dtype, SparseDtype) or not is_extension_array_dtype(pd_dtype):
        # Sparse arrays will be converted later in `check_array`
        # Only handle extension arrays for integer and floats
        return False
    elif is_float_dtype(pd_dtype):
        # Float ndarrays can normally support nans. They need to be converted
        # first to map pd.NA to np.nan
        return True
    elif is_integer_dtype(pd_dtype):
        # XXX: Warn when converting from a high integer to a float
        return True

    return False