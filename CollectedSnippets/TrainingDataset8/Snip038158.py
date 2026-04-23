def __setitem__(self, user_key: str, value: Any) -> None:
        """Set the value of the session_state entry with the given user_key.

        If the key corresponds to a widget or form that's been instantiated
        during the current script run, raise a StreamlitAPIException instead.
        """
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        ctx = get_script_run_ctx()

        if ctx is not None:
            widget_id = self._key_id_mapping.get(user_key, None)
            widget_ids = ctx.widget_ids_this_run
            form_ids = ctx.form_ids_this_run

            if widget_id in widget_ids or user_key in form_ids:
                raise StreamlitAPIException(
                    f"`st.session_state.{user_key}` cannot be modified after the widget"
                    f" with key `{user_key}` is instantiated."
                )

        self._new_session_state[user_key] = value