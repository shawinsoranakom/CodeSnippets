def _get_predictions(self, feed: torch.Tensor) -> npt.NDArray[np.float32]:
        """Obtain preview predictions from the model, chunking feeds into the model's batch size

        Parameters
        ----------
        feed
            The input tensor to obtain predictions from the model in shape (num_sides, N, height,
            width, 3)

        Returns
        -------
        The predictions from the model for the given preview feed
        """
        batch_size = self._plugin.batch_size
        ndim = 4 if mod_cfg.Loss.learn_mask() else 3
        retval = np.empty((feed.shape[0], feed.shape[1], self._out_size, self._out_size, ndim),
                          dtype=np.float32)
        for idx in range(0, feed.shape[1], batch_size):
            feed_batch = feed[:, idx:idx + batch_size]
            feed_size = feed_batch.shape[1]
            is_padded = feed_size < batch_size

            if is_padded:
                holder = torch.empty((feed_batch.shape[0], batch_size, *feed_batch.shape[2:]),
                                     dtype=feed.dtype)
                logger.debug("[Trainer] Padding undersized batch of shape %s to %s",
                             feed_batch.shape, holder.shape)
                holder[:, :feed_size] = feed_batch
                feed_batch = holder
            with torch.inference_mode():
                out = [x.cpu().numpy() for x in self._model.model(list(feed_batch))
                       if x.shape[1] == self._out_size]  # Filter multi-scale output
            if mod_cfg.Loss.learn_mask():  # Apply mask to alpha channel
                out = [np.concatenate(out[i:i + 2], axis=-1) for i in range(0, len(out), 2)]
            out_arr = np.stack(out, axis=0)
            if is_padded:
                out_arr = out_arr[:, :feed_size]
            retval[:, idx:idx + feed_size] = out_arr
        return retval