def frame_meets_criteria(self) -> bool:
        """``True`` if the current frame meets the selected filter criteria otherwise ``False``."""
        filter_mode = self._globals.var_filter_mode.get()
        frame_faces = self._detected_faces.current_faces[self._globals.frame_index]
        distance = self._filter_distance

        retval = (
            filter_mode == "All Frames" or
            (filter_mode == "No Faces" and not frame_faces) or
            (filter_mode == "Has Face(s)" and len(frame_faces) > 0) or
            (filter_mode == "Multiple Faces" and len(frame_faces) > 1) or
            (filter_mode == "Misaligned Faces" and any(face.aligned.average_distance > distance
                                                       for face in frame_faces)))
        assert isinstance(retval, bool)
        logger.trace("filter_mode: %s, frame meets criteria: %s",  # type:ignore[attr-defined]
                     filter_mode, retval)
        return retval