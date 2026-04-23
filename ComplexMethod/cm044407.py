def _get_frame_ranges(self) -> list[tuple[int, int]] | None:
        """Obtain the frame ranges that are to be converted.

        If frame ranges have been specified, then split the command line formatted arguments into
        ranges that can be used.

        Returns
        A list of  frames to be processed, or ``None`` if the command line argument was not used
        """
        if not self._args.frame_ranges:
            logger.debug("No frame range set")
            return None

        min_frame, max_frame = None, None
        if self._images.is_video:
            min_frame, max_frame = 1, self._images.count
        else:
            indices = [int(self._image_idx_re.findall(os.path.basename(filename))[0])
                       for filename in self._images.file_list]
            if indices:
                min_frame, max_frame = min(indices), max(indices)
        logger.debug("min_frame: %s, max_frame: %s", min_frame, max_frame)

        if min_frame is None or max_frame is None:
            raise FaceswapError("Frame Ranges specified, but could not determine frame numbering "
                                "from filenames")

        retval = []
        for rng in self._args.frame_ranges:
            if "-" not in rng:
                raise FaceswapError("Frame Ranges not specified in the correct format")
            start, end = rng.split("-")
            retval.append((max(int(start), min_frame), min(int(end), max_frame)))
        logger.debug("frame ranges: %s", retval)
        return retval