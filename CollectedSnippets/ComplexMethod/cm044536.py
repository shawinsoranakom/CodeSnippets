def load(self) -> bool:
        """ Load the latest training preview image(s) from disk and add to :attr:`buffer` """
        logger.trace("Loading Training preview images")  # type:ignore
        image_files = _get_previews(self._cache_path)
        filename = next((fname for fname in image_files
                         if os.path.basename(fname) == TRAINING_PREVIEW), "")
        img: np.ndarray | None = None
        if not filename:
            logger.trace("No preview to display")  # type:ignore
            return False
        try:
            modified = os.path.getmtime(filename)
            if modified <= self._modified:
                logger.trace("preview '%s' not updated. Current timestamp: %s, "  # type:ignore
                             "existing timestamp: %s", filename, modified, self._modified)
                return False

            logger.debug("Loading preview: '%s'", filename)
            img = cv2.imread(filename, cv2.IMREAD_UNCHANGED)
            assert img is not None
            self._modified = modified
            self._buffer.add_image(os.path.basename(filename), img)
            self._error_count = 0
        except (ValueError, AssertionError):
            # This is probably an error reading the file whilst it's being saved so ignore it
            # for now and only pick up if there have been multiple consecutive fails
            logger.debug("Unable to display preview: (image: '%s', attempt: %s)",
                         img, self._error_count)
            if self._error_count < 10:
                self._error_count += 1
            else:
                logger.error("Error reading the preview file for '%s'", filename)
            return False

        logger.debug("Loaded preview: '%s' (%s)", filename, img.shape)
        return True