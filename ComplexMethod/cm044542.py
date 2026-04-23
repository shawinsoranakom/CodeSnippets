def save(self,
             frame: str,
             idx: int,
             detected_face: DetectedFace,
             frame_dims: tuple[int, int] | None = None) -> None:
        """Build the mask preview image and save

        Parameters
        ----------
        frame
            The frame name in the alignments file
        idx
            The index of the face for this frame in the alignments file
        detected_face
            A detected_face object for a face
        frame_dims
            The size of the original frame, if input is faces otherwise ``None``. Default: ``None``
        """
        assert self._saver is not None

        faces = self._handle_cache(frame, idx, detected_face)
        if not faces:
            return

        mask_types = self._get_mask_types(frame, faces)
        if not faces or not mask_types:
            logger.debug("No valid faces/masks to process for '%s'", frame)
            return

        for mask_type in mask_types:
            detected_faces = [f[1] for f in faces if mask_type in f[1].mask]
            if not detected_face:
                logger.warning("No '%s' masks to output for '%s'", mask_type, frame)
                continue
            if len(detected_faces) != len(faces):
                logger.warning("Some '%s' masks are missing for '%s'", mask_type, frame)

            image = self._create_image(detected_faces, mask_type, frame_dims)
            filename = os.path.splitext(frame)[0]
            if len(mask_types) > 1:
                filename += f"_{mask_type}"
            if not self._full_frame:
                filename += f"_{idx}"
            filename = os.path.join(self._saver.location, f"{filename}.png")
            logger.trace("filename: '%s', image_shape: %s",  # type:ignore[attr-defined]
                         filename, image.shape)
            self._saver.save(filename, image)