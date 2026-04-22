def _raw_session_state() -> SessionState:
    """Return the SessionState instance within the current ScriptRunContext's
    SafeSessionState wrapper.
    """
    return get_session_state()._state