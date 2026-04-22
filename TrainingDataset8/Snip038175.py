def get_session_state() -> SafeSessionState:
    """Get the SessionState object for the current session.

    Note that in streamlit scripts, this function should not be called
    directly. Instead, SessionState objects should be accessed via
    st.session_state.
    """
    global _state_use_warning_already_displayed
    from streamlit.runtime.scriptrunner import get_script_run_ctx

    ctx = get_script_run_ctx()

    # If there is no script run context because the script is run bare, have
    # session state act as an always empty dictionary, and print a warning.
    if ctx is None:
        if not _state_use_warning_already_displayed:
            _state_use_warning_already_displayed = True
            if not runtime.exists():
                LOGGER.warning(
                    "Session state does not function when running a script without `streamlit run`"
                )
        return SafeSessionState(SessionState())
    return ctx.session_state