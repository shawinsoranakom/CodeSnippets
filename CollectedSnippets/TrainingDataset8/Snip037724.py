def _create_new_session_message(self, page_script_hash: str) -> ForwardMsg:
        """Create and return a new_session ForwardMsg."""
        msg = ForwardMsg()

        msg.new_session.script_run_id = _generate_scriptrun_id()
        msg.new_session.name = self._session_data.name
        msg.new_session.main_script_path = self._session_data.main_script_path
        msg.new_session.page_script_hash = page_script_hash

        _populate_app_pages(msg.new_session, self._session_data.main_script_path)
        _populate_config_msg(msg.new_session.config)
        _populate_theme_msg(msg.new_session.custom_theme)

        # Immutable session data. We send this every time a new session is
        # started, to avoid having to track whether the client has already
        # received it. It does not change from run to run; it's up to the
        # to perform one-time initialization only once.
        imsg = msg.new_session.initialize

        _populate_user_info_msg(imsg.user_info)

        imsg.environment_info.streamlit_version = STREAMLIT_VERSION_STRING
        imsg.environment_info.python_version = ".".join(map(str, sys.version_info))

        imsg.session_state.run_on_save = self._run_on_save
        imsg.session_state.script_is_running = (
            self._state == AppSessionState.APP_IS_RUNNING
        )

        imsg.command_line = self._session_data.command_line
        imsg.session_id = self.id

        return msg