def require_valid_user_key(key: str) -> None:
    """Raise an Exception if the given user_key is invalid."""
    if _is_widget_id(key):
        raise StreamlitAPIException(
            f"Keys beginning with {GENERATED_WIDGET_KEY_PREFIX} are reserved."
        )