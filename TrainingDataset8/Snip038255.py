def is_graphviz_chart(
    obj: object,
) -> TypeGuard[Union[graphviz.Graph, graphviz.Digraph]]:
    """True if input looks like a GraphViz chart."""
    return (
        # GraphViz < 0.18
        is_type(obj, "graphviz.dot.Graph")
        or is_type(obj, "graphviz.dot.Digraph")
        # GraphViz >= 0.18
        or is_type(obj, "graphviz.graphs.Graph")
        or is_type(obj, "graphviz.graphs.Digraph")
    )