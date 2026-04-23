def process_folder(self) -> Generator[tuple[str, PNGHeader], None, None]:
        """Iterate through the faces folder pulling out various information for each face.

        Yields
        ------
        A dictionary for each face found containing the keys returned from
        :class:`lib.image.read_image_meta_batch`
        """
        logger.info("Loading file list from %s", self.folder)
        filter_count = 0
        dupe_count = 0
        seen: dict[str, list[int]] = {}

        if self._alignments is not None and self._alignments.version < 2.1:  # Legacy updating
            filelist = [os.path.join(self.folder, face)
                        for face in os.listdir(self.folder)
                        if self.valid_extension(face)]
        else:
            filelist = [os.path.join(self.folder, face)
                        for face in os.listdir(self.folder)
                        if os.path.splitext(face)[-1] == ".png"]

        for fullpath, metadata in tqdm(read_image_meta_batch(filelist),
                                       total=len(filelist),
                                       desc="Reading Face Data"):

            if "itxt" not in metadata or "source" not in metadata["itxt"]:
                logger.warning("Non-Faceswap extracted face found. Image skipped: '%s'",
                               fullpath)
                continue
            sub_dict = T.cast(PNGHeader, PNGHeader.from_dict(metadata["itxt"]))

            if self._handle_duplicate(fullpath, sub_dict, seen):
                dupe_count += 1
                continue

            if (self._alignments is not None and  # filter existing
                    not self._alignments.frame_exists(sub_dict.source.source_filename)):
                filter_count += 1
                continue

            retval = (os.path.basename(fullpath), sub_dict)
            yield retval

        if self._alignments is not None:
            logger.debug("Faces filtered out that did not exist in alignments file: %s",
                         filter_count)

        if dupe_count > 0:
            logger.warning("%s Duplicate face images were found. These files have been moved to "
                           "'%s' from where they can be safely deleted",
                           dupe_count, os.path.join(self.folder, "_duplicates"))