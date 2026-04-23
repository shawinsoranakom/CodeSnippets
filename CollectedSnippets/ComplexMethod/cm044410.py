def _predict_faces(self) -> None:
        """Run Prediction on the Faceswap model in a background thread.

        Reads from the :attr:`self._in_queue`, prepares images for prediction
        then puts the predictions back to the :attr:`self.out_queue`
        """
        faces_seen = 0
        consecutive_no_faces = 0
        batch: list[ConvertItem] = []
        assert self._in_queue is not None
        while True:
            item: T.Literal["EOF"] | ConvertItem = self._in_queue.get()
            if item == "EOF":
                logger.debug("EOF Received")
                if batch:  # Process out any remaining items
                    self._process_batch(batch, faces_seen)
                break
            logger.trace("Got from queue: '%s'", item.inbound.filename)  # type:ignore
            faces_count = len(item.inbound.detected_faces)

            # Safety measure. If a large stream of frames appear that do not have faces,
            # these will stack up into RAM. Keep a count of consecutive frames with no faces.
            # If self._batchsize number of frames appear, force the current batch through
            # to clear RAM.
            consecutive_no_faces = consecutive_no_faces + 1 if faces_count == 0 else 0
            self._faces_count += faces_count
            if faces_count > 1:
                self._verify_output = True
                logger.verbose("Found more than one face in an image! '%s'",  # type:ignore
                               os.path.basename(item.inbound.filename))

            self.load_aligned(item)
            faces_seen += faces_count

            batch.append(item)

            if faces_seen < self._batchsize and consecutive_no_faces < self._batchsize:
                logger.trace("Continuing. Current batchsize: %s, "  # type:ignore
                             "consecutive_no_faces: %s", faces_seen, consecutive_no_faces)
                continue

            self._process_batch(batch, faces_seen)

            consecutive_no_faces = 0
            faces_seen = 0
            batch = []

        logger.debug("Putting EOF")
        self._out_queue.put("EOF")
        logger.debug("Load queue complete")