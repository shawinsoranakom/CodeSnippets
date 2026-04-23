def apply_points_function(
        self,
        func: Callable[[np.ndarray], np.ndarray],
        about_point: Vect3 | None = None,
        about_edge: Vect3 = ORIGIN,
        works_on_bounding_box: bool = False
    ) -> Self:
        if about_point is None and about_edge is not None:
            about_point = self.get_bounding_box_point(about_edge)

        for mob in self.get_family():
            arrs = [mob.data[key] for key in mob.pointlike_data_keys if mob.has_points()]
            if works_on_bounding_box:
                arrs.append(mob.get_bounding_box())

            for arr in arrs:
                if about_point is None:
                    arr[:] = func(arr)
                else:
                    arr[:] = func(arr - about_point) + about_point

        if not works_on_bounding_box:
            self.refresh_bounding_box(recurse_down=True)
        else:
            for parent in self.parents:
                parent.refresh_bounding_box()
        return self