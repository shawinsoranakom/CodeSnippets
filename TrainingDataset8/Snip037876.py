def add_session_ref(self, session: "AppSession", script_run_count: int) -> None:
            """Adds a reference to a AppSession that has referenced
            this Entry's message.

            Parameters
            ----------
            session : AppSession
            script_run_count : int
                The session's run count at the time of the call

            """
            prev_run_count = self._session_script_run_counts.get(session, 0)
            if script_run_count < prev_run_count:
                LOGGER.error(
                    "New script_run_count (%s) is < prev_run_count (%s). "
                    "This should never happen!" % (script_run_count, prev_run_count)
                )
                script_run_count = prev_run_count
            self._session_script_run_counts[session] = script_run_count