def load(self) -> T.Generator[tuple[str, npt.NDArray[np.uint8]] |
                                  tuple[str, npt.NDArray[np.uint8], PNGHeader], None, None]:
        """Generator for loading images from the given :attr:`location`

        If :class:`FacesLoader` is in use then the Faceswap metadata of the image stored in the
        image exif file is added as the final item in the output `tuple`.

        Yields
        ------
        filename
            The filename of the loaded image.
        image
            The loaded image.
        metadata
            The Faceswap metadata associated with the loaded image. (:class:`FacesLoader` only)
        """
        logger.debug("[%s] Initializing Load Generator", self._name)
        self._set_thread()
        assert self._error_state is not None
        while True:
            if self._error_state.has_error:
                current = current_thread()
                if current is main_thread():
                    self._error_state.re_raise()
                else:
                    logger.debug("[%s.%s] Thread error detected in worker thread",
                                 current.name, self._name)
                    break
            try:
                retval = self._queue.get(True, 1)
            except QueueEmpty:
                continue
            if retval == "EOF":
                logger.trace("[%s] Got EOF", self._name)  # type:ignore[attr-defined]
                break
            logger.trace("[%s] Yielding: %s",  # type:ignore[attr-defined]
                         self._name, [v.shape if isinstance(v, np.ndarray) else v for v in retval])
            yield retval
        logger.debug("[%s] Closing Load Generator", self._name)
        self.close()