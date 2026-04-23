def has_session_ref(self, session: "AppSession") -> bool:
            return session in self._session_script_run_counts