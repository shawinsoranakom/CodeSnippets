def set_stroke(
        self,
        color: ManimColor | Iterable[ManimColor] = None,
        width: float | Iterable[float] | None = None,
        opacity: float | Iterable[float] | None = None,
        behind: bool | None = None,
        flat: bool | None = None,
        recurse: bool = True
    ) -> Self:
        self.set_rgba_array_by_color(color, opacity, 'stroke_rgba', recurse)

        if width is not None:
            for mob in self.get_family(recurse):
                data = mob.data if mob.get_num_points() > 0 else mob._data_defaults
                if isinstance(width, (float, int, np.floating)):
                    data['stroke_width'][:, 0] = width
                else:
                    data['stroke_width'][:, 0] = resize_with_interpolation(
                        np.array(width), len(data)
                    ).flatten()

        if behind is not None:
            for mob in self.get_family(recurse):
                if mob.stroke_behind != behind:
                    mob.stroke_behind = behind
                    mob.refresh_shader_wrapper_id()

        if flat is not None:
            self.set_flat_stroke(flat)

        return self