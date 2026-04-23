def _to_numpy(self,
                  data: dict[int, EventData],
                  is_live: bool) -> tuple[np.ndarray, np.ndarray]:
        """ Extract each individual step data into separate numpy arrays for loss and timestamps.

        Timestamps are stored float64 as the extra accuracy is needed for correct timings. Arrays
        are returned at the length of the shortest available data (i.e. truncated records are
        dropped)

        Parameters
        ----------
        data: dict
            The incoming Tensorboard event data in dictionary form per step
        is_live: bool, optional
            ``True`` if the data to be cached is from a live training session otherwise ``False``.
            Default: ``False``

        Returns
        -------
        timestamps: :class:`numpy.ndarray`
            float64 array of all iteration's timestamps
        loss: :class:`numpy.ndarray`
            float32 array of all iteration's loss
        """
        if is_live and self._carry_over:
            logger.debug("Processing carry over: %s", self._carry_over)
            self._collect_carry_over(data)

        times, loss = self._process_data(data, is_live)

        if is_live and not all(len(val) == len(self._loss_labels) for val in loss):
            # TODO Many attempts have been made to fix this for live graph logging, and the issue
            # of non-consistent loss record sizes keeps coming up. In the meantime we shall swallow
            # any loss values that are of incorrect length so graph remains functional. This will,
            # most likely, lead to a mismatch on iteration count so a proper fix should be
            # implemented.

            # Timestamps and loss appears to remain consistent with each other, but sometimes loss
            # appears non-consistent. eg (lengths):
            # [2, 2, 2, 2, 2, 2, 2, 0] - last loss collection has zero length
            # [1, 2, 2, 2, 2, 2, 2, 2] - 1st loss collection has 1 length
            # [2, 2, 2, 3, 2, 2, 2] - 4th loss collection has 3 length

            logger.debug("Inconsistent loss found in collection: %s", loss)
            for idx in reversed(range(len(loss))):
                if len(loss[idx]) != len(self._loss_labels):
                    logger.debug("Removing loss/timestamps at position %s", idx)
                    del loss[idx]
                    del times[idx]

        n_times, n_loss = (np.array(times, dtype="float64"), np.array(loss, dtype="float32"))
        logger.debug("Converted to numpy: (data points: %s, timestamps shape: %s, loss shape: %s)",
                     len(data), n_times.shape, n_loss.shape)

        return n_times, n_loss