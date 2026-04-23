def copy(self, frame_index: int, direction: T.Literal["prev", "next"]) -> None:
        """Copy the alignments from the previous or next frame that has alignments
        to the current frame.

        Parameters
        ----------
        frame_index
            The frame that the needs to have alignments copied to it
        direction
            Whether to copy alignments from the previous frame with alignments, or the next
            frame with alignments
        """
        logger.debug("frame: %s, direction: %s", frame_index, direction)
        faces = self._faces_at_frame_index(frame_index)
        frames_with_faces = [idx for idx, faces in enumerate(self._detected_faces.current_faces)
                             if len(faces) > 0]
        if direction == "prev":
            idx = next((idx for idx in reversed(frames_with_faces)
                        if idx < frame_index), None)
        else:
            idx = next((idx for idx in frames_with_faces
                        if idx > frame_index), None)
        if idx is None:
            # No previous/next frame available
            return
        logger.debug("Copying alignments from frame %s to frame: %s", idx, frame_index)

        # aligned_face cannot be deep copied, so remove and recreate
        to_copy = self._faces_at_frame_index(idx)
        for face in to_copy:
            face._aligned = None  # pylint:disable=protected-access
        copied = deepcopy(to_copy)

        for old_face, new_face in zip(to_copy, copied):
            old_face.load_aligned(None)
            new_face.load_aligned(None)

        faces.extend(copied)
        self._tk_face_count_changed.set(True)
        self._globals.var_full_update.set(True)