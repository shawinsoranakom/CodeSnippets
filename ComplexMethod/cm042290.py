def _render(self, _):
    if DEBUG:
      rl.draw_rectangle_lines_ex(self._rect, 1, rl.RED)

    rl.draw_texture_ex(self._dm_background,
                       rl.Vector2(self._rect.x, self._rect.y), 0.0, 1.0,
                       rl.Color(255, 255, 255, int(255 * self._fade_filter.x)))

    rl.draw_texture_ex(self._dm_person,
                       rl.Vector2(self._rect.x + (self._rect.width - self._dm_person.width) / 2,
                                  self._rect.y + (self._rect.height - self._dm_person.height) / 2), 0.0, 1.0,
                       rl.Color(255, 255, 255, int(255 * 0.9 * self._fade_filter.x)))

    if self.effective_active:
      source_rect = rl.Rectangle(0, 0, self._dm_cone.width, self._dm_cone.height)
      dest_rect = rl.Rectangle(
        self._rect.x + self._rect.width / 2,
        self._rect.y + self._rect.height / 2,
        self._dm_cone.width,
        self._dm_cone.height,
      )

      if not self._lines:
        rl.draw_texture_pro(
          self._dm_cone,
          source_rect,
          dest_rect,
          rl.Vector2(dest_rect.width / 2, dest_rect.height / 2),
          self._rotation_filter.x - 90,
          rl.Color(255, 255, 255, int(255 * self._fade_filter.x)),
        )

      else:
        # remove old angles
        for angle, f in self._head_angles.items():
          dst_from_current = ((angle - self._rotation_filter.x) % 360) - 180
          target = 1.0 if abs(dst_from_current) <= self.LINES_ANGLE_INCREMENT * 5 else 0.0
          if not self._face_detected:
            target = 0.0

          # Reduce all line lengths when looking center
          if self._looking_center:
            target = np.interp(self._looking_center_filter.x, [0.0, 1.0], [target, 0.45])

          f.update(target)
          self._draw_line(angle, f, self._looking_center)