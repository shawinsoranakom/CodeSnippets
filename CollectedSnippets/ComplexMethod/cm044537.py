def _load_images_to_cache(self,  # pylint:disable=too-many-locals
                              image_files: list[str],
                              frame_dims: tuple[int, int],
                              thumbnail_size: int) -> bool:
        """ Load preview images to the image cache.

        Load new images and append to cache, filtering the cache to the number of thumbnails that
        will fit inside the display panel.

        Parameters
        ----------
        image_files: list
            A list of new image files that have been modified since the last check
        frame_dims: tuple
            The (width (`int`), height (`int`)) of the display panel that will display the preview
        thumbnail_size: int
            The size of each thumbnail that should be created

        Returns
        -------
        bool
            ``True`` if images were successfully loaded to cache otherwise ``False``
        """
        logger.debug("Number image_files: %s, frame_dims: %s, thumbnail_size: %s",
                     len(image_files), frame_dims, thumbnail_size)
        num_images = (frame_dims[0] // thumbnail_size) * (frame_dims[1] // thumbnail_size)
        logger.debug("num_images: %s", num_images)
        if num_images == 0:
            return False
        samples: list[np.ndarray] = []
        start_idx = len(image_files) - num_images if len(image_files) > num_images else 0
        show_files = sorted(image_files, key=os.path.getctime)[start_idx:]
        dropped_files = []
        for fname in show_files:
            try:
                img_file = Image.open(fname)
            except PermissionError as err:
                logger.debug("Permission error opening preview file: '%s'. Original error: %s",
                             fname, str(err))
                dropped_files.append(fname)
                continue
            except Exception as err:  # pylint:disable=broad-except
                # Swallow any issues with opening an image rather than spamming console
                # Can happen when trying to read partially saved images
                logger.debug("Error opening preview file: '%s'. Original error: %s",
                             fname, str(err))
                dropped_files.append(fname)
                continue

            width, height = img_file.size
            scaling = thumbnail_size / max(width, height)
            logger.debug("image width: %s, height: %s, scaling: %s", width, height, scaling)

            try:
                img = img_file.resize((int(width * scaling), int(height * scaling)))
            except OSError as err:
                # Image only gets loaded when we call a method, so may error on partial loads
                logger.debug("OS Error resizing preview image: '%s'. Original error: %s",
                             fname, err)
                dropped_files.append(fname)
                continue

            samples.append(self._pad_and_border(img, thumbnail_size))

        return self._process_samples(samples,
                                     [fname for fname in show_files if fname not in dropped_files],
                                     num_images)