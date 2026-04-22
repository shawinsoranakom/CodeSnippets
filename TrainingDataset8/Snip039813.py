def _create_widget(id: str, states: WidgetStates) -> WidgetState:
    """Create a widget with the given ID."""
    states.widgets.add().id = id
    return states.widgets[-1]