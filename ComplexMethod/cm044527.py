def get_data(self, session_id: int, metric: T.Literal["loss", "timestamps"]
                 ) -> dict[int, dict[str, np.ndarray | list[str]]] | None:
        """ Retrieve the decompressed cached data from the cache for the given session id.

        Parameters
        ----------
        session_id: int or ``None``
            If session_id is provided, then the cached data for that session is returned. If
            session_id is ``None`` then the cached data for all sessions is returned
        metric: ['loss', 'timestamps']
            The metric to return the data for.

        Returns
        -------
        dict or ``None``
            The `session_id`(s) as key, the values are a dictionary containing the requested
            metric information for each session returned. ``None`` if no data is stored for the
            given session_id
        """
        if session_id is None:
            raw = self._data
        else:
            data = self._data.get(session_id)
            if not data:
                return None
            raw = {session_id: data}

        retval: dict[int, dict[str, np.ndarray | list[str]]] = {}
        for idx, data in raw.items():
            array = data.loss if metric == "loss" else data.timestamps
            val: dict[str, np.ndarray | list[str]] = {str(metric): array}
            if metric == "loss":
                val["labels"] = data.labels
            retval[idx] = val

        logger.debug("Obtained cached data: %s",
                     {session_id: {k: v.shape if isinstance(v, np.ndarray) else v
                                   for k, v in data.items()}
                      for session_id, data in retval.items()})
        return retval