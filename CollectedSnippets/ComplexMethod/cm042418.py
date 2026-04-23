def _get_scroll(self, visible_items: list[Widget], content_size: float) -> float:
    scroll_enabled = self._scroll_enabled() if callable(self._scroll_enabled) else self._scroll_enabled
    self.scroll_panel.set_enabled(scroll_enabled and self.enabled and not self._scrolling_to[1])
    self.scroll_panel.update(self._rect, content_size)
    if not self._snap_items:
      return self.scroll_panel.get_offset()

    # Snap closest item to center
    center_pos = self._rect.x + self._rect.width / 2 if self._horizontal else self._rect.y + self._rect.height / 2
    closest_delta_pos = float('inf')
    scroll_snap_idx: int | None = None
    for idx, item in enumerate(visible_items):
      if self._horizontal:
        delta_pos = (item.rect.x + item.rect.width / 2) - center_pos
      else:
        delta_pos = (item.rect.y + item.rect.height / 2) - center_pos
      if abs(delta_pos) < abs(closest_delta_pos):
        closest_delta_pos = delta_pos
        scroll_snap_idx = idx

    if scroll_snap_idx is not None:
      snap_item = visible_items[scroll_snap_idx]
      if self.is_pressed:
        # no snapping until released
        self._scroll_snap_filter.x = 0
      else:
        # TODO: this doesn't handle two small buttons at the edges well
        if self._horizontal:
          snap_delta_pos = (center_pos - (snap_item.rect.x + snap_item.rect.width / 2)) / 10
          snap_delta_pos = min(snap_delta_pos, -self.scroll_panel.get_offset() / 10)
          snap_delta_pos = max(snap_delta_pos, (self._rect.width - self.scroll_panel.get_offset() - content_size) / 10)
        else:
          snap_delta_pos = (center_pos - (snap_item.rect.y + snap_item.rect.height / 2)) / 10
          snap_delta_pos = min(snap_delta_pos, -self.scroll_panel.get_offset() / 10)
          snap_delta_pos = max(snap_delta_pos, (self._rect.height - self.scroll_panel.get_offset() - content_size) / 10)
        self._scroll_snap_filter.update(snap_delta_pos)

      self.scroll_panel.set_offset(self.scroll_panel.get_offset() + self._scroll_snap_filter.x)

    return self.scroll_panel.get_offset()