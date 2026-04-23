def _check_and_convert_to_indices(
    opt: Sequence[Any], default_values: Union[Sequence[Any], Any, None]
) -> Optional[List[int]]:
    """Perform validation checks and return indices based on the default values."""
    if default_values is None and None not in opt:
        return None

    if not isinstance(default_values, list):
        # This if is done before others because calling if not x (done
        # right below) when x is of type pd.Series() or np.array() throws a
        # ValueError exception.
        if is_type(default_values, "numpy.ndarray") or is_type(
            default_values, "pandas.core.series.Series"
        ):
            default_values = list(cast(Sequence[Any], default_values))
        elif not default_values or default_values in opt:
            default_values = [default_values]
        else:
            default_values = list(default_values)

    for value in default_values:
        if value not in opt:
            raise StreamlitAPIException(
                "Every Multiselect default value must exist in options"
            )

    return [opt.index(value) for value in default_values]