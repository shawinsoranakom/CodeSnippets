def _render(self, _):
    rl.begin_scissor_mode(int(self._rect.x), int(self._rect.y),
                          int(self._rect.width), int(self._rect.height))

    for item in reversed(self._visible_items):
      if item in self._move_lift:
        continue
      self._render_item(item)

    # Dim background if moving items, lifted items are above
    self._overlay_filter.update(MOVE_OVERLAY_ALPHA if len(self._pending_move) else 0.0)
    if self._overlay_filter.x > 0.01:
      rl.draw_rectangle_rec(self._rect, rl.Color(0, 0, 0, int(255 * self._overlay_filter.x)))

    for item in self._move_lift:
      self._render_item(item)

    rl.end_scissor_mode()

    # Draw edge shadows on top of scroller content
    if self._edge_shadows:
      rl.draw_rectangle_gradient_h(int(self._rect.x), int(self._rect.y),
                                   EDGE_SHADOW_WIDTH, int(self._rect.height),
                                   rl.Color(0, 0, 0, 204), rl.BLANK)

      right_x = int(self._rect.x + self._rect.width - EDGE_SHADOW_WIDTH)
      rl.draw_rectangle_gradient_h(right_x, int(self._rect.y),
                                   EDGE_SHADOW_WIDTH, int(self._rect.height),
                                   rl.BLANK, rl.Color(0, 0, 0, 204))

    # Draw scroll indicator on top of edge shadows
    if self._show_scroll_indicator and len(self._visible_items) > 0:
      self._scroll_indicator.update(self._scroll_offset, self._content_size, self._rect)
      self._scroll_indicator.render()