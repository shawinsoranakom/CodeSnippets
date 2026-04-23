def _process(self, queue: Queue) -> None:
        """The load thread.

        Loads from a folder of images or from a video and puts to a queue

        Parameters
        ----------
        queue
            The ImageIO Queue
        """
        iterator = self._from_video if self._is_video else self._from_folder
        logger.debug("[%s] Load iterator: %s", self._name, iterator)
        assert self._error_state is not None
        for retval in iterator():
            filename, image = retval[:2]
            if image is None or (not image.any() and image.ndim not in (2, 3)):
                # All black frames will return not numpy.any() so check dims too
                logger.warning("Unable to open image. Skipping: '%s'", filename)
                continue
            logger.trace("[%s] Putting to queue: %s",  # type:ignore[attr-defined]
                         self._name, [v.shape if isinstance(v, np.ndarray) else v for v in retval])

            while True:
                if self._error_state.has_error:
                    logger.debug("[%s] Thread error detected in worker thread", self._name)
                    return
                try:
                    queue.put(retval, timeout=0.2)
                    break
                except QueueFull:
                    logger.trace("[%s] Queue full. Waiting",  # type:ignore[attr-defined]
                                 self._name)
                    continue
        logger.trace("[%s] Putting EOF", self._name)  # type:ignore[attr-defined]
        queue.put("EOF")