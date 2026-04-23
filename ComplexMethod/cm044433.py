def _save(self,
              filename: str,
              image: bytes | np.ndarray,
              sub_folder: str | None) -> None:
        """ Save a single image inside a ThreadPoolExecutor

        Parameters
        ----------
        filename: str
            The filename of the image to be saved. NB: Any folders passed in with the filename
            will be stripped and replaced with :attr:`location`.
        image: bytes or :class:`numpy.ndarray`
            The encoded image or numpy array to be saved
        subfolder: str or ``None``
            If the file should be saved in a subfolder in the output location, the subfolder should
            be provided here. ``None`` for no subfolder.
        """
        location = os.path.join(self.location, sub_folder) if sub_folder else self._location
        if sub_folder and not os.path.exists(location):
            os.makedirs(location)

        filename = os.path.join(location, os.path.basename(filename))
        try:
            if self._as_bytes:
                assert isinstance(image, bytes)
                with open(filename, "wb") as out_file:
                    out_file.write(image)
            else:
                assert isinstance(image, np.ndarray)
                cv2.imwrite(filename, image)
            logger.trace("[%s] Saved image: '%s'",  # type:ignore[attr-defined]
                         self._name, filename)
        except Exception as err:  # pylint:disable=broad-except
            logger.error("Failed to save image '%s'. Original Error: %s", filename, str(err))
        del image
        del filename