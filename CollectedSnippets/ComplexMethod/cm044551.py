def update(self) -> None:
        """ Load and unload thumbnails in the visible area of the faces viewer. """
        if self._canvas.optional_annotations["mesh"]:  # Display any hidden end of row meshes
            self._canvas.itemconfig("viewport_mesh", state="normal")

        self._visible_grid, self._visible_faces = self._grid.visible_area
        if (np.any(self._images) and np.any(self._visible_grid)
                and self._visible_grid.shape[1:] != self._images.shape):
            self._reset_viewport()

        required_rows = self._visible_grid.shape[1] if self._grid.is_valid else 0
        existing_rows = len(self._images)
        logger.trace("existing_rows: %s. required_rows: %s",  # type:ignore[attr-defined]
                     existing_rows, required_rows)

        if existing_rows > required_rows:
            self._remove_rows(existing_rows, required_rows)
        if existing_rows < required_rows:
            self._add_rows(existing_rows, required_rows)

        self._shift()