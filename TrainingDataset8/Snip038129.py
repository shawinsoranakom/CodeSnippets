def _is_internal_key(key: str) -> bool:
    return key.startswith(STREAMLIT_INTERNAL_KEY_PREFIX)