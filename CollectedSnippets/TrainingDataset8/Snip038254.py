def is_plotly_chart(obj: object) -> TypeGuard[Union[Figure, list[Any], dict[str, Any]]]:
    """True if input looks like a Plotly chart."""
    return (
        is_type(obj, "plotly.graph_objs._figure.Figure")
        or _is_list_of_plotly_objs(obj)
        or _is_probably_plotly_dict(obj)
    )