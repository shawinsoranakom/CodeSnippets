def check_session_state_rules(
    default_value: Any, key: Optional[str], writes_allowed: bool = True
) -> None:
    global _shown_default_value_warning

    if key is None or not runtime.exists():
        return

    session_state = get_session_state()
    if not session_state.is_new_state_value(key):
        return

    if not writes_allowed:
        raise StreamlitAPIException(
            "Values for st.button, st.download_button, st.file_uploader, and "
            "st.form cannot be set using st.session_state."
        )

    if default_value is not None and not _shown_default_value_warning:
        streamlit.warning(
            f'The widget with key "{key}" was created with a default value but'
            " also had its value set via the Session State API."
        )
        _shown_default_value_warning = True