def marshall(
    proto: BokehChartProto,
    figure: "Figure",
    use_container_width: bool,
    element_id: str,
) -> None:
    """Construct a Bokeh chart object.

    See DeltaGenerator.bokeh_chart for docs.
    """
    from bokeh.embed import json_item

    data = json_item(figure)
    proto.figure = json.dumps(data)
    proto.use_container_width = use_container_width
    proto.element_id = element_id