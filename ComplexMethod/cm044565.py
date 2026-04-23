def _find_alignments(self) -> str:
        """ If an alignments folder is required and hasn't been provided, scan for a file based on
        the video folder.

        Exits if an alignments file cannot be located

        Returns
        -------
        str
            The full path to an alignments file
        """
        fname = self._args.alignments_file
        frames = self._args.frames_dir
        if fname and os.path.isfile(fname) and os.path.splitext(fname)[-1].lower() == ".fsa":
            return fname
        if fname:
            logger.error("Not a valid alignments file: '%s'", fname)
            sys.exit(1)

        if not frames or not os.path.exists(frames):
            logger.error("Not a valid frames folder: '%s'. Can't scan for alignments.", frames)
            sys.exit(1)

        fname = "alignments.fsa"
        if os.path.isdir(frames) and os.path.exists(os.path.join(frames, fname)):
            return os.path.join(frames, fname)

        if os.path.isdir(frames) or os.path.splitext(frames)[-1] not in VIDEO_EXTENSIONS:
            logger.error("Can't find a valid alignments file in location: %s", frames)
            sys.exit(1)

        fname = f"{os.path.splitext(frames)[0]}_{fname}"
        if not os.path.exists(fname):
            logger.error("Can't find a valid alignments file for video: %s", frames)
            sys.exit(1)

        return fname