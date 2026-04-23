def _place_previews(self, frame_dims: tuple[int, int]) -> Image.Image | None:
        """ Format the preview thumbnails stored in the cache into a grid fitting the display
        panel.

        Parameters
        ----------
        frame_dims: tuple
            The (width (`int`), height (`int`)) of the display panel that will display the preview

        Returns
        -------
        :class:`PIL.Image`: | None
            The final preview display image
        """
        if self._images is None:
            logger.debug("No images in cache. Returning None")
            return None
        samples = self._images.copy()
        num_images, thumbnail_size = samples.shape[:2]
        if self._placeholder is None:
            self._create_placeholder(thumbnail_size)

        logger.debug("num_images: %s, thumbnail_size: %s", num_images, thumbnail_size)
        cols, rows = frame_dims[0] // thumbnail_size, frame_dims[1] // thumbnail_size
        logger.debug("cols: %s, rows: %s", cols, rows)
        if cols == 0 or rows == 0:
            logger.debug("Cols or Rows is zero. No items to display")
            return None

        remainder = (cols * rows) - num_images
        if remainder != 0:
            logger.debug("Padding sample display. Remainder: %s", remainder)
            assert self._placeholder is not None
            placeholder = np.concatenate([np.expand_dims(self._placeholder, 0)] * remainder)
            samples = np.concatenate((samples, placeholder))

        display = np.vstack([np.hstack(T.cast("Sequence", samples[row * cols: (row + 1) * cols]))
                             for row in range(rows)])
        logger.debug("display shape: %s", display.shape)
        return Image.fromarray(display)