def _get_pandas_index_attr(
    data: "Union[DataFrame, Series]",
    attr: str,
) -> Optional[Any]:
    return getattr(data.index, attr, None)