def _check_cache(self, session_id: int | None = None) -> None:
        """ Check if the given session_id has been cached and if not, cache it.

        Parameters
        ----------
        session_id: int, optional
            The Session ID to return the data for. Set to ``None`` to return all session
            data. Default ``None`
        """
        if session_id is not None and not self._cache.is_cached(session_id):
            self._cache_data(session_id)
        elif self._is_training and session_id == self.session_ids[-1]:
            self._cache_data(session_id)
        elif session_id is None:
            for idx in self.session_ids:
                if not self._cache.is_cached(idx):
                    self._cache_data(idx)