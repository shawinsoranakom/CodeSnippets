def _get_time_stats(self) -> None:
        """ Populates the attribute :attr:`_time_stats` with the start start time, end time and
        data points for each session id within the loaded session if it has not already been
        calculated.

        If the main Session is currently training, then the training session ID is updated with the
        latest stats.
        """
        if not self._time_stats:
            logger.debug("Collating summary time stamps")

            self._time_stats = {
                sess_id: {"start_time": np.min(timestamps) if np.any(timestamps) else 0,
                          "end_time": np.max(timestamps) if np.any(timestamps) else 0,
                          "iterations": timestamps.shape[0] if np.any(timestamps) else 0}
                for sess_id, timestamps in T.cast(dict[int, np.ndarray],
                                                  self._session.get_timestamps(None)).items()}

        elif _SESSION.is_training:
            logger.debug("Updating summary time stamps for training session")

            session_id = _SESSION.session_ids[-1]
            latest = T.cast(np.ndarray, self._session.get_timestamps(session_id))

            self._time_stats[session_id] = {
                "start_time": np.min(latest) if np.any(latest) else 0,
                "end_time": np.max(latest) if np.any(latest) else 0,
                "iterations": latest.shape[0] if np.any(latest) else 0}

        logger.debug("time_stats: %s", self._time_stats)