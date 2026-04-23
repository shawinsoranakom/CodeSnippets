def process(self, batch: ExtractBatch) -> None:
        """Obtain the output from the plugin's model.

        Executes the plugin's predict function and stores the output prior to post-processing.

        If rotations have been selected, plugin post-processing is done as part of this process as
        the computed bounding boxes are required for re-feeding the model future rotations

        Parameters
        ----------
        batch
            The incoming ExtractBatch to use for processing
        """
        process = "process"
        input_images = batch.data
        batch_size = input_images.shape[0]
        box_list: list[None | np.ndarray] = [None for _ in range(batch_size)]
        boxes: np.ndarray | None = None
        indices_angle = np.zeros((batch_size, ), dtype="int32")

        idx = 0
        mask_requires = np.array([True for _ in range(batch_size)])
        while True:
            feed = self._rotator.rotate(idx, input_images[mask_requires])
            if feed is None:
                logger.trace(  # type:ignore[attr-defined]
                    "[%s.%s] No faces found in %s image(s) of %s after %s rotations: %s",
                    self.plugin.name,
                    process,
                    mask_requires.sum(),
                    batch_size,
                    idx,
                    batch.filenames)

                break
            result = self._predict(feed)
            if not self._rotator.enabled:
                # Not rotating. Do post-processing in next thread
                boxes = result
                break

            # We are rotating, so we have to do post-processing here, to re-feed model
            self._process_rotations(result, mask_requires, indices_angle, box_list, idx)
            if not np.any(mask_requires):
                logger.trace(  # type:ignore[attr-defined]
                    "[%s.%s] Found faces for all %s images after %s rotations: %s",
                    self.plugin.name,
                    process,
                    batch_size,
                    idx + 1,
                    batch.filenames)
                break
            idx += 1

        boxes = (np.array([self._empty_bbox if b is None else b for b in box_list],
                          dtype="object")
                 if boxes is None else boxes)
        batch.data = np.empty(2, dtype="object")
        batch.data[0] = indices_angle
        batch.data[1] = boxes