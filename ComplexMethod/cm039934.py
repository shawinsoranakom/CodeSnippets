def test_convert_container(
    constructor_name,
    container_type,
    dtype,
    superdtype,
):
    """Check that we convert the container to the right type of array with the
    right data type."""
    if constructor_name in (
        "dataframe",
        "index",
        "polars",
        "polars_series",
        "pyarrow",
        "pyarrow_array",
        "series",
    ):
        # delay the import of pandas/polars within the function to only skip this test
        # instead of the whole file
        container_type = container_type()
    container = [0, 1]

    container_converted = _convert_container(
        container,
        constructor_name,
        dtype=dtype,
    )
    assert isinstance(container_converted, container_type)

    if constructor_name in ("list", "tuple", "index"):
        # list and tuple will use Python class dtype: int, float
        # pandas index will always use high precision: np.int64 and np.float64
        assert np.issubdtype(type(container_converted[0]), superdtype)
    elif constructor_name in ("polars", "polars_series", "pyarrow", "pyarrow_array"):
        return
    elif hasattr(container_converted, "dtype"):
        assert container_converted.dtype == dtype
    elif hasattr(container_converted, "dtypes"):
        assert container_converted.dtypes[0] == dtype