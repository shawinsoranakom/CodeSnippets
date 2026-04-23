def _get_locations(self) -> dict[str, list[str | None]]:
        """ Obtain the full path to any frame, face and alignments input locations for the
        selected job when running in batch mode. If not running in batch mode, then the original
        passed in values are returned in lists

        Returns
        -------
        dict[str, list[Optional[str]]]
            A dictionary corresponding to the alignments, frames_dir and faces_dir arguments
            with a list of full paths for each job
        """
        job: str = self._args.job
        if not self._batch_mode:  # handle with given arguments
            retval = {"alignments_file": [self._args.alignments_file],
                      "faces_dir": [self._args.faces_dir],
                      "frames_dir": [self._args.frames_dir]}

        elif job in self._requires_alignments:  # Jobs only requiring an alignments file location
            retval = self._get_alignments_locations()

        elif job in self._requires_frames:  # Jobs that require a frames folder
            retval = self._get_frames_locations()

        elif job in self._requires_faces and job not in self._requires_frames:
            # Jobs that require faces as input
            faces = [os.path.join(self._args.faces_dir, folder)
                     for folder in os.listdir(self._args.faces_dir)
                     if os.path.isdir(os.path.join(self._args.faces_dir, folder))]
            if not faces:
                logger.error("No folders found in '%s'", self._args.faces_dir)
                sys.exit(1)

            retval = {"faces_dir": faces,
                      "frames_dir": [None for _ in range(len(faces))],
                      "alignments_file": [None for _ in range(len(faces))]}
            logger.info("Batch mode selected. Processing faces: %s",
                        [os.path.basename(folder) for folder in faces])
        else:
            raise FaceswapError(f"Unhandled job: {self._args.job}. This is a bug. Please report "
                                "to the developers")

        logger.debug("File locations: %s", retval)
        return retval