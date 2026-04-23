def get_graph_label(
        self,
        graph: ParametricCurve,
        label: str | Mobject = "f(x)",
        x: float | None = None,
        direction: Vect3 = RIGHT,
        buff: float = MED_SMALL_BUFF,
        color: ManimColor | None = None
    ) -> Tex | Mobject:
        if isinstance(label, str):
            label = Tex(label)
        if color is None:
            label.match_color(graph)
        if x is None:
            # Searching from the right, find a point
            # whose y value is in bounds
            max_y = FRAME_Y_RADIUS - label.get_height()
            max_x = FRAME_X_RADIUS - label.get_width()
            for x0 in np.arange(*self.x_range)[::-1]:
                pt = self.i2gp(x0, graph)
                if abs(pt[0]) < max_x and abs(pt[1]) < max_y:
                    x = x0
                    break
            if x is None:
                x = self.x_range[1]

        point = self.input_to_graph_point(x, graph)
        angle = self.angle_of_tangent(x, graph)
        normal = rotate_vector(RIGHT, angle + 90 * DEG)
        if normal[1] < 0:
            normal *= -1
        label.next_to(point, normal, buff=buff)
        label.shift_onto_screen()
        return label