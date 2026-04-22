def _is_keyed_widget_id(key: str) -> bool:
    return _is_widget_id(key) and not key.endswith("-None")