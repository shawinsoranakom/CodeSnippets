def count(self) -> int:
        """The number of frames that meet the filter criteria returned by
        :attr:`~tools.manual.manual.TkGlobals.var_filter_mode.get()`."""
        face_count_per_index = self._detected_faces.face_count_per_index
        if self._globals.var_filter_mode.get() == "No Faces":
            retval = sum(1 for f_count in face_count_per_index if f_count == 0)
        elif self._globals.var_filter_mode.get() == "Has Face(s)":
            retval = sum(1 for f_count in face_count_per_index if f_count != 0)
        elif self._globals.var_filter_mode.get() == "Multiple Faces":
            retval = sum(1 for f_count in face_count_per_index if f_count > 1)
        elif self._globals.var_filter_mode.get() == "Misaligned Faces":
            distance = self._filter_distance
            retval = sum(1 for frame in self._detected_faces.current_faces
                         if any(face.aligned.average_distance > distance for face in frame))
        else:
            retval = len(face_count_per_index)
        logger.trace("filter mode: %s, frame count: %s",  # type:ignore[attr-defined]
                     self._globals.var_filter_mode.get(), retval)
        return retval