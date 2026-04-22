def _get_widget(id: str, states: WidgetStates) -> Optional[WidgetState]:
    """Return the widget with the given ID."""
    for state in states.widgets:
        if state.id == id:
            return state
    return None