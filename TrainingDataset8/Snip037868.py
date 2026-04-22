def add_message(
        self, msg: ForwardMsg, session: "AppSession", script_run_count: int
    ) -> None:
        """Add a ForwardMsg to the cache.

        The cache will also record a reference to the given AppSession,
        so that it can track which sessions have already received
        each given ForwardMsg.

        Parameters
        ----------
        msg : ForwardMsg
        session : AppSession
        script_run_count : int
            The number of times the session's script has run

        """
        populate_hash_if_needed(msg)
        entry = self._entries.get(msg.hash, None)
        if entry is None:
            entry = ForwardMsgCache.Entry(msg)
            self._entries[msg.hash] = entry
        entry.add_session_ref(session, script_run_count)