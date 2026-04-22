def remove_session_ref(self, session: "AppSession") -> None:
            del self._session_script_run_counts[session]