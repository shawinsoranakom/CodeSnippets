def _render(self, rect: rl.Rectangle) -> None:
    # adjust y pos with torque
    torque_line_offset = np.interp(abs(self._torque_filter.x), [0.5, 1], [22, 26])
    torque_line_height = np.interp(abs(self._torque_filter.x), [0.5, 1], [14, 56])

    # animate alpha and angle span
    if not self._demo:
      self._torque_line_alpha_filter.update(ui_state.status != UIStatus.DISENGAGED)
    else:
      self._torque_line_alpha_filter.update(1.0)

    torque_line_bg_alpha = np.interp(abs(self._torque_filter.x), [0.5, 1.0], [0.25, 0.5])
    torque_line_bg_color = rl.Color(255, 255, 255, int(255 * torque_line_bg_alpha * self._torque_line_alpha_filter.x))
    if ui_state.status != UIStatus.ENGAGED and not self._demo:
      torque_line_bg_color = rl.Color(255, 255, 255, int(255 * 0.15 * self._torque_line_alpha_filter.x))

    # draw curved line polygon torque bar
    torque_line_radius = 1200
    top_angle = -90
    torque_bg_angle_span = self._torque_line_alpha_filter.x * TORQUE_ANGLE_SPAN
    torque_start_angle = top_angle - torque_bg_angle_span / 2
    torque_end_angle = top_angle + torque_bg_angle_span / 2
    # centerline radius & center (you already have these values)
    mid_r = torque_line_radius + torque_line_height / 2

    cx = rect.x + rect.width / 2 + 8  # offset 8px to right of camera feed
    cy = rect.y + rect.height + torque_line_radius - torque_line_offset

    # draw bg torque indicator line
    bg_pts = arc_bar_pts(cx, cy, mid_r, torque_line_height, torque_start_angle, torque_end_angle)
    draw_polygon(rect, bg_pts, color=torque_line_bg_color)

    # draw torque indicator line
    a0s = top_angle
    a1s = a0s + torque_bg_angle_span / 2 * self._torque_filter.x
    sl_pts = arc_bar_pts(cx, cy, mid_r, torque_line_height, a0s, a1s)

    # draw beautiful gradient from center to 65% of the bg torque bar width
    start_grad_pt = cx / rect.width
    if self._torque_filter.x < 0:
      end_grad_pt = (cx * (1 - 0.65) + (min(bg_pts[:, 0]) * 0.65)) / rect.width
    else:
      end_grad_pt = (cx * (1 - 0.65) + (max(bg_pts[:, 0]) * 0.65)) / rect.width

    # fade to orange as we approach max torque
    start_color = blend_colors(
      rl.Color(255, 255, 255, int(255 * 0.9 * self._torque_line_alpha_filter.x)),
      rl.Color(255, 200, 0, int(255 * self._torque_line_alpha_filter.x)),  # yellow
      max(0, abs(self._torque_filter.x) - 0.75) * 4,
    )
    end_color = blend_colors(
      rl.Color(255, 255, 255, int(255 * 0.9 * self._torque_line_alpha_filter.x)),
      rl.Color(255, 115, 0, int(255 * self._torque_line_alpha_filter.x)),  # orange
      max(0, abs(self._torque_filter.x) - 0.75) * 4,
    )

    if ui_state.status != UIStatus.ENGAGED and not self._demo:
      start_color = end_color = rl.Color(255, 255, 255, int(255 * 0.35 * self._torque_line_alpha_filter.x))

    gradient = Gradient(
      start=(start_grad_pt, 0),
      end=(end_grad_pt, 0),
      colors=[
        start_color,
        end_color,
      ],
      stops=[0.0, 1.0],
    )

    draw_polygon(rect, sl_pts, gradient=gradient)

    # draw center torque bar dot
    if abs(self._torque_filter.x) < 0.5:
      dot_y = self._rect.y + self._rect.height - torque_line_offset - torque_line_height / 2
      rl.draw_circle(int(cx), int(dot_y), 10 // 2,
                     rl.Color(182, 182, 182, int(255 * 0.9 * self._torque_line_alpha_filter.x)))