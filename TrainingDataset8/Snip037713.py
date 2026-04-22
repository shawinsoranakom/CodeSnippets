def _create_scriptrunner(self, initial_rerun_data: RerunData) -> None:
        """Create and run a new ScriptRunner with the given RerunData."""
        self._scriptrunner = ScriptRunner(
            session_id=self.id,
            main_script_path=self._session_data.main_script_path,
            client_state=self._client_state,
            session_state=self._session_state,
            uploaded_file_mgr=self._uploaded_file_mgr,
            initial_rerun_data=initial_rerun_data,
            user_info=self._user_info,
        )
        self._scriptrunner.on_event.connect(self._on_scriptrunner_event)
        self._scriptrunner.start()