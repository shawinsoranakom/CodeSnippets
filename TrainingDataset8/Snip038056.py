def enqueue(self, msg: ForwardMsg) -> None:
        """Enqueue a ForwardMsg for this context's session."""
        if msg.HasField("page_config_changed") and not self._set_page_config_allowed:
            raise StreamlitAPIException(
                "`set_page_config()` can only be called once per app, "
                + "and must be called as the first Streamlit command in your script.\n\n"
                + "For more information refer to the [docs]"
                + "(https://docs.streamlit.io/library/api-reference/utilities/st.set_page_config)."
            )

        # We want to disallow set_page config if one of the following occurs:
        # - set_page_config was called on this message
        # - The script has already started and a different st call occurs (a delta)
        if msg.HasField("page_config_changed") or (
            msg.HasField("delta") and self._has_script_started
        ):
            self._set_page_config_allowed = False

        # Pass the message up to our associated ScriptRunner.
        self._enqueue(msg)