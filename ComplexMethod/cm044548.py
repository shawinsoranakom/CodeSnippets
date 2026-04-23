def frames_list(self) -> list[int]:
        """The list of frame indices that meet the filter criteria returned by
        :attr:`~tools.manual.manual.TkGlobals.var_filter_mode.get()`. """
        face_count_per_index = self._detected_faces.face_count_per_index
        if self._globals.var_filter_mode.get() == "No Faces":
            retval = [idx for idx, count in enumerate(face_count_per_index) if count == 0]
        elif self._globals.var_filter_mode.get() == "Multiple Faces":
            retval = [idx for idx, count in enumerate(face_count_per_index) if count > 1]
        elif self._globals.var_filter_mode.get() == "Has Face(s)":
            retval = [idx for idx, count in enumerate(face_count_per_index) if count != 0]
        elif self._globals.var_filter_mode.get() == "Misaligned Faces":
            distance = self._filter_distance
            retval = [idx for idx, frame in enumerate(self._detected_faces.current_faces)
                      if any(face.aligned.average_distance > distance for face in frame)]
        else:
            retval = list(range(len(face_count_per_index)))
        logger.trace("filter mode: %s, number_frames: %s",  # type:ignore[attr-defined]
                     self._globals.var_filter_mode.get(), len(retval))
        return retval