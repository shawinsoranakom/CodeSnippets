def _update_viewport(self, refresh_annotations: bool) -> None:
        """ Update the viewport

        Parameters
        ----------
        refresh_annotations: bool
            ``True`` if mesh annotations should be re-calculated otherwise ``False``

        Clear out cached objects that are not currently in view. Populate the cache for any
        faces that are now in view. Populate the correct face image and annotations for each
        object in the viewport based on current location. If optional mesh annotations are
        enabled, then calculates newly displayed meshes. """
        if not self._grid.is_valid:
            return
        self._discard_tk_faces()

        for collection in zip(self._objects.visible_grid.transpose(1, 2, 0),
                              self._objects.images,
                              self._objects.meshes,
                              self._objects.visible_faces):
            for (frame_idx, face_idx, pnt_x, pnt_y), image_id, mesh_ids, face in zip(*collection):
                if frame_idx == self._active_frame.frame_index and not refresh_annotations:
                    logger.trace("Skipping active frame: %s",  # type:ignore[attr-defined]
                                 frame_idx)
                    continue
                if frame_idx == -1:
                    logger.trace("Blanking non-existant face")  # type:ignore[attr-defined]
                    self._canvas.itemconfig(image_id, image="")
                    for area in mesh_ids.values():
                        for mesh_id in area:
                            self._canvas.itemconfig(mesh_id, state="hidden")
                    continue

                tk_face = self.get_tk_face(frame_idx, face_idx, face)
                self._canvas.itemconfig(image_id, image=tk_face.photo)

                if (self._canvas.optional_annotations["mesh"]
                        or frame_idx == self._active_frame.frame_index
                        or refresh_annotations):
                    landmarks = self.get_landmarks(frame_idx, face_idx, face, [pnt_x, pnt_y],
                                                   refresh=True)
                    self._locate_mesh(mesh_ids, landmarks)