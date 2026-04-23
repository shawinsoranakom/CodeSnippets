def _is_widget_id(key: str) -> bool:
    return key.startswith(GENERATED_WIDGET_KEY_PREFIX)