def interpolate(
        self,
        mobject1: Mobject,
        mobject2: Mobject,
        alpha: float,
        path_func: Callable[[np.ndarray, np.ndarray, float], np.ndarray] = straight_path
    ) -> Self:
        keys = [k for k in self.data.dtype.names if k not in self.locked_data_keys]
        if keys:
            self.note_changed_data()
        for key in keys:
            md1 = mobject1.data[key]
            md2 = mobject2.data[key]
            if key in self.const_data_keys:
                md1 = md1[0]
                md2 = md2[0]
            if key in self.pointlike_data_keys:
                self.data[key] = path_func(md1, md2, alpha)
            else:
                self.data[key] = (1 - alpha) * md1 + alpha * md2

        for key in self.uniforms:
            if key in self.locked_uniform_keys:
                continue
            if key not in mobject1.uniforms or key not in mobject2.uniforms:
                continue
            self.uniforms[key] = (1 - alpha) * mobject1.uniforms[key] + alpha * mobject2.uniforms[key]
        self.bounding_box[:] = path_func(mobject1.bounding_box, mobject2.bounding_box, alpha)
        return self