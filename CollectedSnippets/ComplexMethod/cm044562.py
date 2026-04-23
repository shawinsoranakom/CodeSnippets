def _get_alignments_locations(self) -> dict[str, list[str | None]]:
        """ Obtain the full path to alignments files in a parent (batch) location

        These are jobs that only require an alignments file as input, so frames and face locations
        are returned as a list of ``None`` values corresponding to the number of alignments files
        detected

        Returns
        -------
        dict[str, list[Optional[str]]]:
            The list of alignments location paths and None lists for frames and faces locations
        """
        if not self._args.alignments_file:
            logger.error("Please provide an 'alignments_file' location for '%s' job",
                         self._args.job)
            sys.exit(1)

        alignments = [os.path.join(self._args.alignments_file, fname)
                      for fname in os.listdir(self._args.alignments_file)
                      if os.path.splitext(fname)[-1].lower() == ".fsa"
                      and os.path.splitext(fname)[0].endswith("alignments")]
        if not alignments:
            logger.error("No alignment files found in '%s'", self._args.alignments_file)
            sys.exit(1)

        logger.info("Batch mode selected. Processing alignments: %s", alignments)
        retval = {"alignments_file": alignments,
                  "faces_dir": [None for _ in range(len(alignments))],
                  "frames_dir": [None for _ in range(len(alignments))]}
        return retval