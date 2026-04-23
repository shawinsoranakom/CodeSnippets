def is_type(
    obj: object, fqn_type_pattern: Literal["plotly.graph_objs._figure.Figure"]
) -> TypeGuard[Figure]:
    ...