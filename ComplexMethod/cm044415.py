def _set_skip_list(self) -> None:
        """ Add the skip list to the image loader

        Checks against `extract_every_n` and the existence of alignments data (can exist if
        `skip_existing` or `skip_existing_faces` has been provided) and compiles a list of frame
        indices that should not be processed, providing these to :class:`lib.image.ImagesLoader`.
        """
        existing = list(self._alignments)
        if self._extract_every == 1 and not existing:
            logger.debug("[Extract.Loader] No frames to be skipped")
            self._ready = True
            return

        skip_een = set(i for i in range(self._images.count) if i % self._extract_every != 0)

        file_names = ([os.path.basename(f) for f in self._images.file_list]
                      if self._skip_frames or self._skip_faces else [])
        skip_frames = set(i for i, f in enumerate(file_names)
                          if f in existing) if self._skip_frames else set()
        skip_faces = (
            set(i for i, f in enumerate(file_names)
                if f in self._alignments and self._alignments[f].faces)
            if self._skip_faces else set()
        )
        skip_exist = skip_frames.union(skip_faces)

        if self._extract_every > 1:
            logger.info("Skipping %s frames of %s for extract every %s",
                        len(skip_een), self._images.count, self._extract_every)
        if skip_exist:
            self.existing_count = len(skip_exist.difference(skip_een))
            logger.info("Skipping %s frames of %s for skip existing frames/faces",
                        self.existing_count, self._images.count - len(skip_een))

        skip = list(skip_exist.union(skip_een))
        logger.debug("[Extract.Loader] Total skip count: %s", len(skip))
        self._images.add_skip_list(skip)
        self._ready = True