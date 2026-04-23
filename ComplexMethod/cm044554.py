def _show_mesh(self,
                   mesh_ids: dict[T.Literal["polygon", "line"], list[int]],
                   face_index: int,
                   detected_face: DetectedFace,
                   top_left: list[float]) -> None:
        """ Display the mesh annotation for the given face, at the given location.

        Parameters
        ----------
        mesh_ids: dict[Literal["polygon", "line"], list[int]]
            Dictionary containing the `polygon` and `line` tkinter canvas identifiers that make up
            the mesh for the given face
        face_index: int
            The face index within the frame for the given face
        detected_face: :class:`~lib.align.DetectedFace`
            The detected face object that contains the landmarks for generating the mesh
        top_left: list[float]
            The (x, y) top left co-ordinates of the mesh's bounding box
        """
        state = "normal" if (self._tk_vars["selected_editor"].get() != "Mask" or
                             self._optional_annotations["mesh"]) else "hidden"
        kwargs: dict[T.Literal["polygon", "line"], dict[str, T.Any]] = {
            "polygon": {"fill": "", "width": 2, "outline": self._canvas.control_colors["Mesh"]},
            "line": {"fill": self._canvas.control_colors["Mesh"], "width": 2}}

        assert isinstance(self._tk_vars["edited"], tk.BooleanVar)
        edited = (self._tk_vars["edited"].get() and
                  self._tk_vars["selected_editor"].get() not in ("Mask", "View"))
        landmarks = self._viewport.get_landmarks(self.frame_index,
                                                 face_index,
                                                 detected_face,
                                                 top_left,
                                                 edited)
        for key, kwarg in kwargs.items():
            if key not in mesh_ids:
                continue
            for idx, mesh_id in enumerate(mesh_ids[key]):
                self._canvas.coords(mesh_id, *landmarks[key][idx].flatten())
                self._canvas.itemconfig(mesh_id, state=state, **kwarg)
                self._canvas.addtag_withtag(f"active_mesh_{key}", mesh_id)