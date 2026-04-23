def _get_frames_locations(self) -> dict[str, list[str | None]]:
        """ Obtain the full path to frame locations along with corresponding alignments file
        locations contained within the parent (batch) location

        Returns
        -------
        dict[str, list[Optional[str]]]:
            list of frames and alignments location paths. If the job requires an output faces
            location then the faces folders are also returned, otherwise the faces will be a list
            of ``Nones`` corresponding to the number of jobs to run
        """
        if not self._args.frames_dir:
            logger.error("Please provide a 'frames_dir' location for '%s' job", self._args.job)
            sys.exit(1)

        frames: list[str] = []
        alignments: list[str] = []
        candidates = [os.path.join(self._args.frames_dir, fname)
                      for fname in os.listdir(self._args.frames_dir)
                      if os.path.isdir(os.path.join(self._args.frames_dir, fname))
                      or os.path.splitext(fname)[-1].lower() in VIDEO_EXTENSIONS]
        logger.debug("Frame candidates: %s", candidates)

        for candidate in candidates:
            fname = os.path.join(candidate, "alignments.fsa")
            if os.path.isdir(candidate) and os.path.exists(fname):
                frames.append(candidate)
                alignments.append(fname)
                continue
            fname = f"{os.path.splitext(candidate)[0]}_alignments.fsa"
            if os.path.isfile(candidate) and os.path.exists(fname):
                frames.append(candidate)
                alignments.append(fname)
                continue
            logger.warning("Can't locate alignments file for '%s'. Skipping.", candidate)

        if not frames:
            logger.error("No valid videos or frames folders found in '%s'", self._args.frames_dir)
            sys.exit(1)

        if self._args.job not in self._requires_faces:  # faces not required for frames input
            faces: list[str | None] = [None for _ in range(len(frames))]
        else:
            if not self._args.faces_dir:
                logger.error("Please provide a 'faces_dir' location for '%s' job", self._args.job)
                sys.exit(1)
            faces = [os.path.join(self._args.faces_dir, os.path.basename(os.path.splitext(frm)[0]))
                     for frm in frames]

        logger.info("Batch mode selected. Processing frames: %s",
                    [os.path.basename(frame) for frame in frames])

        return {"alignments_file": T.cast(list[str | None], alignments),
                "frames_dir": T.cast(list[str | None], frames),
                "faces_dir": faces}