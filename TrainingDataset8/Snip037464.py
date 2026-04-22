def marshall(
    proto: GraphVizChartProto,
    figure_or_dot: FigureOrDot,
    use_container_width: bool,
    element_id: str,
) -> None:
    """Construct a GraphViz chart object.

    See DeltaGenerator.graphviz_chart for docs.
    """

    if type_util.is_graphviz_chart(figure_or_dot):
        dot = figure_or_dot.source
    elif isinstance(figure_or_dot, str):
        dot = figure_or_dot
    else:
        raise StreamlitAPIException(
            "Unhandled type for graphviz chart: %s" % type(figure_or_dot)
        )

    proto.spec = dot
    proto.use_container_width = use_container_width
    proto.element_id = element_id