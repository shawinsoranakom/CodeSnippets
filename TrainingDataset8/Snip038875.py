def _get_data_frame(delta: Delta, name: Optional[str] = None) -> DataFrame:
    """Extract the dataframe protobuf from a delta protobuf."""
    delta_type = delta.WhichOneof("type")

    if delta_type == "new_element":
        element_type = delta.new_element.WhichOneof("type")

        # Some element types don't support named datasets.
        if name and element_type in ("data_frame", "table", "chart"):
            raise ValueError("Dataset names not supported for st.%s" % element_type)

        if element_type in "data_frame":
            return delta.new_element.data_frame
        elif element_type in "table":
            return delta.new_element.table
        elif element_type == "chart":
            return delta.new_element.chart.data
        elif element_type == "vega_lite_chart":
            chart_proto = delta.new_element.vega_lite_chart
            if name:
                return _get_or_create_dataset(chart_proto.datasets, name)
            elif len(chart_proto.datasets) == 1:
                # Support the case where the dataset name was randomly given by
                # the charting library (e.g. Altair) and the user has no
                # knowledge of it.
                return chart_proto.datasets[0].data
            else:
                return chart_proto.data
        # TODO: Support DeckGL. Need to figure out how to handle layer indices
        # first.

    elif delta_type == "add_rows":
        if delta.add_rows.has_name and name != delta.add_rows.name:
            raise ValueError('No dataset found with name "%s".' % name)
        return delta.add_rows.data
    else:
        raise ValueError("Cannot extract DataFrame from %s." % delta_type)