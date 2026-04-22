def has_message_reference(
        self, msg: ForwardMsg, session: "AppSession", script_run_count: int
    ) -> bool:
        """Return True if a session has a reference to a message."""
        populate_hash_if_needed(msg)

        entry = self._entries.get(msg.hash, None)
        if entry is None or not entry.has_session_ref(session):
            return False

        # Ensure we're not expired
        age = entry.get_session_ref_age(session, script_run_count)
        return age <= int(config.get_option("global.maxCachedMessageAge"))