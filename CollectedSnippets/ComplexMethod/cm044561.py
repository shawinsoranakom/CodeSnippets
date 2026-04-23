def _drag_stop_selected(self):
        """ Action to perform when mouse drag is stopped in selected points editor mode.

        If there is already a selection, update the viewport thumbnail

        If this is a new selection, then obtain the selected points and track
        """
        if "face_index" in self._drag_data:  # Selected data has been moved
            self._det_faces.update.post_edit_trigger(self._globals.frame_index,
                                                     self._drag_data["face_index"])
            return

        # This is a new selection
        face_idx = set()
        landmark_indices = []

        for item_id in self._canvas.find_withtag("lm_selected"):
            tags = self._canvas.gettags(item_id)
            face_idx.add(next(int(tag.split("_")[-1])
                              for tag in tags if tag.startswith("face_")))
            landmark_indices.append(next(int(tag.split("_")[-1])
                                         for tag in tags
                                         if tag.startswith("lm_dsp_") and "face" not in tag))
        if len(face_idx) != 1:
            logger.trace("Not exactly 1 face in selection. Aborting. Face indices: %s", face_idx)
            self._reset_selection()
            return

        self._drag_data["face_index"] = face_idx.pop()
        self._drag_data["landmarks"] = landmark_indices
        self._canvas.itemconfig(self._selection_box, stipple="", fill="", outline="#ffff00")
        self._snap_selection_to_points()