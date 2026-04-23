def _render(self, _):
    # TODO: don't draw items that are not in the viewport
    visible_items = [item for item in self._items if item.is_visible]

    # Add line separator between items
    if self._line_separator is not None:
      l = len(visible_items)
      for i in range(1, len(visible_items)):
        visible_items.insert(l - i, self._line_separator)

    content_height = sum(item.rect.height for item in visible_items) + self._spacing * (len(visible_items))
    if not self._pad_end:
      content_height -= self._spacing
    scroll = self.scroll_panel.update(self._rect, rl.Rectangle(0, 0, self._rect.width, content_height))

    rl.begin_scissor_mode(int(self._rect.x), int(self._rect.y),
                          int(self._rect.width), int(self._rect.height))

    cur_height = 0
    for idx, item in enumerate(visible_items):
      if not item.is_visible:
        continue

      # Nicely lay out items vertically
      x = self._rect.x
      y = self._rect.y + cur_height + self._spacing * (idx != 0)
      cur_height += item.rect.height + self._spacing * (idx != 0)

      # Consider scroll
      y += scroll

      # Update item state
      item.set_position(x, y)
      item.set_parent_rect(self._rect)
      item.render()

    rl.end_scissor_mode()