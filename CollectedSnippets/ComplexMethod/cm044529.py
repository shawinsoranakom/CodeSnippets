def get_loss(self, session_id: int | None = None) -> dict[int, dict[str, np.ndarray]]:
        """ Read the loss from the TensorBoard event logs

        Parameters
        ----------
        session_id: int, optional
            The Session ID to return the loss for. Set to ``None`` to return all session
            losses. Default ``None``

        Returns
        -------
        dict
            The session id(s) as key, with a further dictionary as value containing the loss name
            and list of loss values for each step
        """
        logger.debug("Getting loss: (session_id: %s)", session_id)
        retval: dict[int, dict[str, np.ndarray]] = {}
        for idx in [session_id] if session_id else self.session_ids:
            self._check_cache(idx)
            full_data = self._cache.get_data(idx, "loss")
            if not full_data:
                continue
            data = full_data[idx]
            loss = data["loss"]
            assert isinstance(loss, np.ndarray)
            retval[idx] = {title: loss[:, idx] for idx, title in enumerate(data["labels"])}

        logger.debug({key: {k: v.shape for k, v in val.items()}
                      for key, val in retval.items()})
        return retval