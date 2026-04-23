def load_latest_preview(self, thumbnail_size: int, frame_dims: tuple[int, int]) -> bool:
        """ Load the latest preview image for extract and convert.

        Retrieves the latest preview images from the faceswap output folder, resizes to thumbnails
        and lays out for display. Places the images into :attr:`preview_image` for loading into
        the display panel.

        Parameters
        ----------
        thumbnail_size: int
            The size of each thumbnail that should be created
        frame_dims: tuple
            The (width (`int`), height (`int`)) of the display panel that will display the preview

        Returns
        -------
        bool
            ``True`` if a preview was successfully loaded otherwise ``False``
        """
        logger.debug("Loading preview image: (thumbnail_size: %s, frame_dims: %s)",
                     thumbnail_size, frame_dims)
        image_path = self._get_newest_folder() if self._batch_mode else self._output_path
        image_files = _get_previews(image_path)
        gui_preview = os.path.join(self._output_path, ".gui_preview.jpg")
        if not image_files or (len(image_files) == 1 and gui_preview not in image_files):
            logger.debug("No preview to display")
            return False
        # Filter to just the gui_preview if it exists in folder output
        image_files = [gui_preview] if gui_preview in image_files else image_files
        logger.debug("Image Files: %s", len(image_files))

        image_files = self._get_newest_filenames(image_files)
        if not image_files:
            return False

        if not self._load_images_to_cache(image_files, frame_dims, thumbnail_size):
            logger.debug("Failed to load any preview images")
            if gui_preview in image_files:
                # Reset last modified for failed loading of a gui preview image so it is picked
                # up next time
                self._modified = 0.0
            return False

        if image_files == [gui_preview]:
            # Delete the preview image so that the main scripts know to output another
            logger.debug("Deleting preview image")
            os.remove(image_files[0])
        show_image = self._place_previews(frame_dims)
        if not show_image:
            self._preview_image = None
            self._preview_image_tk = None
            return False

        logger.debug("Displaying preview: %s", self._filenames)
        self._preview_image = show_image
        self._preview_image_tk = ImageTk.PhotoImage(show_image)
        return True