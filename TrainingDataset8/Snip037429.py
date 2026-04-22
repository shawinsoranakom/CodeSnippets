def _get_pydeck_tooltip(pydeck_obj: Optional["Deck"]) -> Optional[Dict[str, str]]:
    if pydeck_obj is None:
        return None

    # For pydeck <0.8.1 or pydeck>=0.8.1 when jupyter extra is installed.
    desk_widget = getattr(pydeck_obj, "deck_widget", None)
    if desk_widget is not None and isinstance(desk_widget.tooltip, dict):
        return desk_widget.tooltip

    # For pydeck >=0.8.1 when jupyter extra is not installed.
    # For details, see: https://github.com/visgl/deck.gl/pull/7125/files
    tooltip = getattr(pydeck_obj, "_tooltip", None)
    if tooltip is not None and isinstance(tooltip, dict):
        return tooltip

    return None