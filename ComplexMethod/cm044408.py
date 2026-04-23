def _load(self, *args) -> None:  # pylint:disable=unused-argument
        """Load frames from disk.

        In a background thread:
            * Loads frames from disk.
            * Discards or passes through cli selected skipped frames
            * Pairs the frame with its :class:`~lib.align.DetectedFace` objects
            * Performs any pre-processing actions
            * Puts the frame and detected faces to the load queue
        """
        logger.debug("Load Images: Start")
        idx = 0
        for filename_image in self._images.load():
            idx += 1
            filename, image = filename_image[:2]
            if self._queues["load"].shutdown_event.is_set():
                logger.debug("Load Queue: Stop signal received. Terminating")
                break
            if image is None or (not image.any() and image.ndim not in (2, 3)):
                # All black frames will return not numpy.any() so check dims too
                logger.warning("Unable to open image. Skipping: '%s'", filename)
                continue
            if self._check_skip_frame(filename):
                if self._args.keep_unchanged:
                    logger.trace("Saving unchanged frame: %s", filename)  # type:ignore
                    out_file = os.path.join(self._args.output_dir, os.path.basename(filename))
                    self._queues["save"].put((out_file, image))
                else:
                    logger.trace("Discarding frame: '%s'", filename)  # type:ignore
                continue

            detected_faces = self._get_detected_faces(filename, image)
            frame_faces = FrameFaces(filename, image)
            frame_faces.detected_faces = detected_faces
            item = ConvertItem(frame_faces)

            self._queues["load"].put(item)

        logger.debug("Putting EOF")
        self._queues["load"].put("EOF")
        logger.debug("Load Images: Complete")