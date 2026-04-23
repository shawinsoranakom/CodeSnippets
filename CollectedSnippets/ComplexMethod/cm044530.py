def get_loss(self, session_id: int | None) -> dict[str, np.ndarray]:
        """ Obtain the loss values for the given session_id.

        Parameters
        ----------
        session_id: int or ``None``
            The session ID to return loss for. Pass ``None`` to return loss for all sessions.

        Returns
        -------
        dict
            Loss names as key, :class:`numpy.ndarray` as value. If No session ID was provided
            all session's losses are collated
        """
        self._wait_for_thread()

        if self._is_training:
            self._is_querying.set()

        assert self._tb_logs is not None
        loss_dict = self._tb_logs.get_loss(session_id=session_id)
        if session_id is None:
            all_loss: dict[str, list[float]] = {}
            for key in sorted(loss_dict):
                for loss_key, loss in loss_dict[key].items():
                    all_loss.setdefault(loss_key, []).extend(loss)
            retval: dict[str, np.ndarray] = {key: np.array(val, dtype="float32")
                                             for key, val in all_loss.items()}
        else:
            retval = loss_dict.get(session_id, {})

        if self._is_training:
            self._is_querying.clear()
        return retval