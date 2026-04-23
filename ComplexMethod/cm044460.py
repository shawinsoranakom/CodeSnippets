def _predict(self, feed: np.ndarray) -> np.ndarray:
        """Obtain a prediction from the plugin

        Parameters
        ----------
        feed
            The batch to feed the model

        Returns
        -------
        The prediction from the model

        Raises
        ------
        FaceswapError
            If an OOM occurs
        """
        feed_size = feed.shape[0]
        is_padded = self.do_compile and feed_size < self.plugin.batch_size
        batch_feed = feed
        if is_padded:  # Prevent model re-compile on undersized batch
            batch_feed = np.empty((self.plugin.batch_size, *feed.shape[1:]), dtype=feed.dtype)
            logger.debug("[%s.process] Padding undersized batch of shape %s to %s",
                         self.plugin.name, feed.shape, batch_feed.shape)
            batch_feed[:feed_size] = feed
        try:
            retval = self.plugin.process(batch_feed)
        except OutOfMemoryError as err:
            raise FaceswapError(OOM_MESSAGE) from err
        if is_padded and retval.dtype == "object":
            out = np.empty(retval.shape, dtype="object")
            out[:] = [x[:feed_size] for x in retval]
            retval = out
        elif is_padded:
            retval = retval[:feed_size]
        return retval