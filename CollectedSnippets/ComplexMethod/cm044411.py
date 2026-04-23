def _get_face_metadata(self) -> dict[str, list[int]]:
        """Check for the existence of an aligned directory for identifying which faces in the
        target frames should be swapped. If it exists, scan the folder for face's metadata

        Returns
        -------
        Dictionary of source frame names with a list of associated face indices to be skipped
        """
        retval: dict[str, list[int]] = {}
        input_aligned_dir = self._args.input_aligned_dir

        if input_aligned_dir is None:
            logger.verbose("Aligned directory not specified. All faces listed in "  # type:ignore
                           "the alignments file will be converted")
            return retval
        if not os.path.isdir(input_aligned_dir):
            logger.warning("Aligned directory not found. All faces listed in the "
                           "alignments file will be converted")
            return retval

        filelist = get_image_paths(input_aligned_dir)
        for fullpath, metadata in tqdm(read_image_meta_batch(filelist),
                                       total=len(filelist),
                                       desc="Reading Face Data",
                                       leave=False):
            if "itxt" not in metadata or "source" not in metadata["itxt"]:
                logger.warning("Non-Faceswap extracted face found. Image skipped: '%s'",
                               fullpath)
                continue
            meta = metadata["itxt"]["source"]
            retval.setdefault(meta["source_filename"], []).append(meta["face_index"])

        if not retval:
            raise FaceswapError("Aligned directory is empty, no faces will be converted!")
        if len(retval) <= len(self._input_images) / 3:
            logger.warning("Aligned directory contains far fewer images than the input "
                           "directory, are you sure this is the right folder?")
        return retval