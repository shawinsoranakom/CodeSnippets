def _wait_for_threads(self, extractor: Aligner, loader: FrameLoader, valid_meta: bool) -> None:
        """The :class:`Aligner` and :class:`FramesLoader` are launched in background threads.
        Wait for them to be initialized prior to proceeding.

        Parameters
        ----------
        extractor
            The extraction pipeline for the Manual Tool
        loader
            The frames loader for the Manual Tool
        valid_meta
            Whether the input video had valid meta-data on import, or if it had to be created.
            ``True`` if valid meta data existed previously, ``False`` if it needed to be created

        Notes
        -----
        Because some of the initialize checks perform extra work once their threads are complete,
        they should only return ``True`` once, and should not be queried again.
        """
        extractor_init = False
        frames_init = False
        while True:
            extractor_init = extractor_init if extractor_init else extractor.is_initialized
            frames_init = frames_init if frames_init else loader.is_initialized
            if extractor_init and frames_init:
                logger.debug("Threads initialized")
                break
            logger.debug("Threads not initialized. Waiting...")
            sleep(1)

        extractor.link_faces(self._detected_faces)
        if not valid_meta and loader.video_meta_data:
            logger.debug("Saving video meta data to alignments file")
            self._detected_faces.save_video_meta_data(
                pts_time=loader.video_meta_data["pts_time"],
                keyframes=loader.video_meta_data["keyframes"]
                )