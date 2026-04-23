def _create_widget(id: str, states: WidgetStates) -> WidgetState:
    """
    Returns
    -------
    streamlit.proto.WidgetStates_pb2.WidgetState

    """
    states.widgets.add().id = id
    return states.widgets[-1]