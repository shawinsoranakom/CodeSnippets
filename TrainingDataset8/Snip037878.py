def get_session_ref_age(
            self, session: "AppSession", script_run_count: int
        ) -> int:
            """The age of the given session's reference to the Entry,
            given a new script_run_count.

            """
            return script_run_count - self._session_script_run_counts[session]