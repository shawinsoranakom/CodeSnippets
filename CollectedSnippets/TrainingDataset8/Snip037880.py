def has_refs(self) -> bool:
            """True if this Entry has references from any AppSession.

            If not, it can be removed from the cache.
            """
            return len(self._session_script_run_counts) > 0