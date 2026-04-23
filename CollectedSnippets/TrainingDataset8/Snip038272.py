def _is_colum_type_arrow_incompatible(column: Union[Series, Index]) -> bool:
    """Return True if the column type is known to cause issues during Arrow conversion."""

    # Check all columns for mixed types and complex128 type
    # The dtype of mixed type columns is always object, the actual type of the column
    # values can be determined via the infer_dtype function:
    # https://pandas.pydata.org/docs/reference/api/pandas.api.types.infer_dtype.html

    return (
        column.dtype == "object" and infer_dtype(column) in ["mixed", "mixed-integer"]
    ) or column.dtype == "complex128"