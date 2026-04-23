def _set_timelapse(self) -> bool:
        """Validate timelapse settings

        Returns
        -------
        ``True`` if timelapse is enabled and valid otherwise ``False``
        """
        if (not self._args.timelapse_input_a and
                not self._args.timelapse_input_b and
                not self._args.timelapse_output):
            return False
        if (not self._args.timelapse_input_a or
                not self._args.timelapse_input_b or
                not self._args.timelapse_output):
            raise FaceswapError("To enable the timelapse, you have to supply all the parameters "
                                "(--timelapse-input-A, --timelapse-input-B and "
                                "--timelapse-output).")

        timelapse_folders = [self._args.timelapse_input_a, self._args.timelapse_input_b]
        get_folder(self._args.timelapse_output)

        for idx, folder in enumerate(timelapse_folders):
            side = "a" if idx == 0 else "b"
            if folder is not None and not os.path.isdir(folder):
                raise FaceswapError(f"The Timelapse path '{folder}' does not exist")

            training_folder = getattr(self._args, f"input_{side}")
            if folder == training_folder:
                continue  # Time-lapse folder is training folder

            filenames = [os.path.join(folder, fname) for fname in os.listdir(folder)
                         if os.path.splitext(fname)[-1].lower() == ".png"]
            if not filenames:
                raise FaceswapError(f"The Timelapse path '{folder}' does not contain any valid "
                                    "images")

            self._validate_faceswap_image(filenames[0])
        logger.debug("[Train] Timelapse enabled")
        return True