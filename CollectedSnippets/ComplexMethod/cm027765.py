def get_riemann_rectangles(
        self,
        graph: ParametricCurve,
        x_range: Sequence[float] = None,
        dx: float | None = None,
        input_sample_type: str = "left",
        stroke_width: float = 1,
        stroke_color: ManimColor = BLACK,
        fill_opacity: float = 1,
        colors: Iterable[ManimColor] = (BLUE, GREEN),
        negative_color: ManimColor = RED,
        stroke_background: bool = True,
        show_signed_area: bool = True
    ) -> VGroup:
        if x_range is None:
            x_range = self.x_range[:2]
        if dx is None:
            dx = self.x_range[2]
        if len(x_range) < 3:
            x_range = [*x_range, dx]

        rects = []
        x_range[1] = x_range[1] + dx
        xs = np.arange(*x_range)
        for x0, x1 in zip(xs, xs[1:]):
            if input_sample_type == "left":
                sample = x0
            elif input_sample_type == "right":
                sample = x1
            elif input_sample_type == "center":
                sample = 0.5 * x0 + 0.5 * x1
            else:
                raise Exception("Invalid input sample type")
            height_vect = self.i2gp(sample, graph) - self.c2p(sample, 0)
            rect = Rectangle(
                width=self.x_axis.n2p(x1)[0] - self.x_axis.n2p(x0)[0],
                height=get_norm(height_vect),
            )
            rect.positive = height_vect[1] > 0
            rect.move_to(self.c2p(x0, 0), DL if rect.positive else UL)
            rects.append(rect)
        result = VGroup(*rects)
        result.set_submobject_colors_by_gradient(*colors)
        result.set_style(
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            fill_opacity=fill_opacity,
            stroke_behind=stroke_background
        )
        for rect in result:
            if not rect.positive:
                rect.set_fill(negative_color)
        return result