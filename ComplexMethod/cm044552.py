def _add_rows(self, existing_rows: int, required_rows: int) -> None:
        """ Add rows to the viewport.

        Parameters
        ----------
        existing_rows: int
            The number of existing rows within the viewport
        required_rows: int
            The number of rows required by the viewport
        """
        logger.debug("Adding rows to viewport: (existing_rows: %s, required_rows: %s)",
                     existing_rows, required_rows)
        columns = self._grid.columns_rows[0]

        base_coords: list[list[float | int]]

        if not np.any(self._images):
            base_coords = [[col * self._size, 0] for col in range(columns)]
        else:
            base_coords = [self._canvas.coords(item_id) for item_id in self._images[0]]
        logger.trace("existing rows: %s, required_rows: %s, "  # type:ignore[attr-defined]
                     "base_coords: %s", existing_rows, required_rows, base_coords)
        images = []
        meshes = []
        for row in range(existing_rows, required_rows):
            y_coord = base_coords[0][1] + (row * self._size)
            images.append([self._recycler.get_image((coords[0], y_coord))
                           for coords in base_coords])
            meshes.append([{} if face is None else self._recycler.get_mesh(face)
                           for face in self._visible_faces[row]])

        a_images: np.ndarray = np.array(images)
        a_meshes: np.ndarray = np.array(meshes)

        if not np.any(self._images):
            logger.debug("Adding initial viewport objects: (image shapes: %s, mesh shapes: %s)",
                         a_images.shape, a_meshes.shape)
            self._images = a_images
            self._meshes = a_meshes
        else:
            logger.debug("Adding new viewport objects: (image shapes: %s, mesh shapes: %s)",
                         a_images.shape, a_meshes.shape)
            self._images = np.concatenate((self._images, a_images))
            self._meshes = np.concatenate((self._meshes, a_meshes))

        logger.trace("self._images: %s, self._meshes: %s",  # type:ignore[attr-defined]
                     self._images.shape, self._meshes.shape)