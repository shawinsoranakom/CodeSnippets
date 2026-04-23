def _layout(self):
    self._visible_items = [item for item in self._items if item.is_visible]

    self._content_size = sum(item.rect.width if self._horizontal else item.rect.height for item in self._visible_items)
    self._content_size += self._spacing * (len(self._visible_items) - 1)
    self._content_size += self._pad * 2

    self._scroll_offset = self._get_scroll(self._visible_items, self._content_size)

    self._item_pos_filter.update(self._scroll_offset)

    cur_pos = 0
    for idx, item in enumerate(self._visible_items):
      spacing = self._spacing if (idx > 0) else self._pad
      # Nicely lay out items horizontally/vertically
      if self._horizontal:
        x = self._rect.x + cur_pos + spacing
        y = self._rect.y + (self._rect.height - item.rect.height) / 2
        cur_pos += item.rect.width + spacing
      else:
        x = self._rect.x + (self._rect.width - item.rect.width) / 2
        y = self._rect.y + cur_pos + spacing
        cur_pos += item.rect.height + spacing

      # Consider scroll
      if self._horizontal:
        x += self._scroll_offset
      else:
        y += self._scroll_offset

      # Add some jello effect when scrolling
      if DO_JELLO:
        if self._horizontal:
          cx = self._rect.x + self._rect.width / 2
          jello_offset = self._scroll_offset - np.interp(x + item.rect.width / 2,
                                                         [self._rect.x, cx, self._rect.x + self._rect.width],
                                                         [self._item_pos_filter.x, self._scroll_offset, self._item_pos_filter.x])
          x -= np.clip(jello_offset, -20, 20)
        else:
          cy = self._rect.y + self._rect.height / 2
          jello_offset = self._scroll_offset - np.interp(y + item.rect.height / 2,
                                                         [self._rect.y, cy, self._rect.y + self._rect.height],
                                                         [self._item_pos_filter.x, self._scroll_offset, self._item_pos_filter.x])
          y -= np.clip(jello_offset, -20, 20)

      # Animate moves if needed
      x, y = self._do_move_animation(item, x, y)

      # Update item state
      item.set_position(x, y)
      item.set_parent_rect(self._rect)