def put_direct(self,  # noqa[C901]
                   filename: str,
                   image: npt.NDArray[np.uint8],
                   detected_faces: list[DetectedFace],
                   is_aligned: bool = False,
                   frame_size: tuple[int, int] | None = None) -> ExtractBatch:
        """Put an item directly into this runner's plugin and return the result

        Parameters
        ----------
        filename
            The filename of the frame
        image
            The loaded frame as UINT8 BGR array
        detected_faces
            The detected face objects for the frame
        is_aligned
            ``True`` if the image being passed into the pipeline is an aligned faceswap face.
            Default: ``False``
        frame_size
            The (height, width) size of the original frame if passing in an aligned image

        Raises
        ------
        ValueError
            If attempting to put an ExtractBatch object to the first runner in the pipeline or if
            providing an aligned image with insufficient data

        Returns
        -------
        ExtractBatch
            The output from this plugin for the given input
        """
        if isinstance(self._inbound_iterator, InputIterator):
            raise ValueError("'put_direct' should not be used on the first runner in a "
                             "pipeline. Use the runner's `put` method")
        if self.handler.plugin_type not in ("detect", "align") and not is_aligned:
            raise ValueError(f"'{self.handler.plugin_type}' requires aligned input")
        if self.handler.plugin_type in ("detect", "align") and is_aligned:
            raise ValueError(f"'{self.handler.plugin_type}' requires non-aligned input")
        if is_aligned and not frame_size:
            raise ValueError("Aligned input must provide the original frame_size")
        batch = ExtractBatch(filenames=[filename], images=[image], is_aligned=is_aligned)
        batch.bboxes = np.array([[f.left, f.top, f.right, f.bottom]
                                 for f in detected_faces], dtype=np.int32)
        batch.frame_ids = np.zeros((batch.bboxes.shape[0], ), dtype=np.int32)
        batch.frame_sizes = [frame_size] if frame_size else None
        if self.handler.plugin_type not in ("detect", "align"):
            landmarks = np.array([f.landmarks_xy for f in detected_faces], dtype=np.float32)
            batch.landmarks = landmarks
            batch.landmark_type = LandmarkType.from_shape(T.cast(tuple[int, int],
                                                                 landmarks.shape[1:]))
        original_out = self._queues["out"]  # Unhook queue from next runner
        self._queues["out"] = Queue(maxsize=1)
        self._put_to_input(batch)
        self._put_to_input(ExtractSignal.FLUSH)

        result: list[ExtractBatch] = []
        while True:
            if self._threads.error_state.has_error and current_thread() == main_thread():
                self._threads.error_state.re_raise()
            if self._threads.error_state.has_error:
                logger.debug("[%s.%s] Thread error detected in worker thread",
                             current_thread().name, self.__class__.__name__)
                break
            try:
                out = self._queues["out"].get(timeout=0.2)
            except QueueEmpty:
                continue
            if out == ExtractSignal.FLUSH:
                break
            result.append(out)

        self._queues["out"] = original_out  # Re-attach queue to next runner

        retval = result[0]
        if len(result) > 1:
            for remain in result[1:]:
                retval.append(remain)
        return retval