def extract_face(self, image: np.ndarray | None) -> np.ndarray | None:
        """Extract the face from a source image and populate :attr:`face`. If an image is not
        provided then ``None`` is returned.

        Parameters
        ----------
        image
            The original frame to extract the face from. ``None`` if the face should not be
            extracted

        Returns
        -------
        The extracted face at the given size, with the given coverage of the given dtype or
        ``None`` if no image has been provided.
        """
        if image is None:
            logger.trace("_extract_face called without a loaded "  # type:ignore[attr-defined]
                         "image. Returning empty face.")
            return None

        if self._is_aligned:
            # Crop out the sub face from full head
            image = self._convert_centering(image)

        if self._is_aligned and image.shape[0] != self._size:  # Resize the given aligned face
            interpolation = cv2.INTER_CUBIC if image.shape[0] < self._size else cv2.INTER_AREA
            retval = cv2.resize(image, (self._size, self._size), interpolation=interpolation)
        elif self._is_aligned:
            retval = image
        else:
            mat = self.matrix
            if self.y_offset:
                mat = self.matrix.copy()
                mat[1, 2] += self.y_offset
            retval = transform_image(image, mat, self._size, self.padding)
        retval = retval if self._dtype is None else retval.astype(self._dtype)
        return retval