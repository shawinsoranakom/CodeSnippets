def _render(self, _):
    # Text can be a callable
    # TODO: cache until text changed
    self._update_text(self._text)

    text_size = self._text_size[0] if self._text_size else rl.Vector2(0.0, 0.0)
    if self._text_alignment_vertical == rl.GuiTextAlignmentVertical.TEXT_ALIGN_MIDDLE:
      total_text_height = sum(ts.y for ts in self._text_size) or self._font_size * FONT_SCALE
      text_pos = rl.Vector2(self._rect.x, (self._rect.y + (self._rect.height - total_text_height) // 2))
    else:
      text_pos = rl.Vector2(self._rect.x, self._rect.y)

    if self._icon:
      icon_y = self._rect.y + (self._rect.height - self._icon.height) / 2
      if len(self._text_wrapped) > 0:
        if self._text_alignment == rl.GuiTextAlignment.TEXT_ALIGN_LEFT:
          icon_x = self._rect.x + self._text_padding
          text_pos.x = self._icon.width + ICON_PADDING
        elif self._text_alignment == rl.GuiTextAlignment.TEXT_ALIGN_CENTER:
          total_width = self._icon.width + ICON_PADDING + text_size.x
          icon_x = self._rect.x + (self._rect.width - total_width) / 2
          text_pos.x = self._icon.width + ICON_PADDING
        else:
          icon_x = (self._rect.x + self._rect.width - text_size.x - self._text_padding) - ICON_PADDING - self._icon.width
      else:
        icon_x = self._rect.x + (self._rect.width - self._icon.width) / 2
      rl.draw_texture_v(self._icon, rl.Vector2(icon_x, icon_y), rl.WHITE)

    for text, text_size, emojis in zip_longest(self._text_wrapped, self._text_size, self._emojis, fillvalue=[]):
      line_pos = rl.Vector2(text_pos.x, text_pos.y)
      if self._text_alignment == rl.GuiTextAlignment.TEXT_ALIGN_LEFT:
        line_pos.x += self._text_padding
      elif self._text_alignment == rl.GuiTextAlignment.TEXT_ALIGN_CENTER:
        line_pos.x += (self._rect.width - text_size.x) // 2
      elif self._text_alignment == rl.GuiTextAlignment.TEXT_ALIGN_RIGHT:
        line_pos.x += self._rect.width - text_size.x - self._text_padding

      prev_index = 0
      for start, end, emoji in emojis:
        text_before = text[prev_index:start]
        width_before = measure_text_cached(self._font, text_before, self._font_size)
        rl.draw_text_ex(self._font, text_before, line_pos, self._font_size, 0, self._text_color)
        line_pos.x += width_before.x

        tex = emoji_tex(emoji)
        rl.draw_texture_ex(tex, line_pos, 0.0, self._font_size / tex.height * FONT_SCALE, self._text_color)
        line_pos.x += self._font_size * FONT_SCALE
        prev_index = end
      rl.draw_text_ex(self._font, text[prev_index:], line_pos, self._font_size, 0, self._text_color)
      text_pos.y += (text_size.y or self._font_size * FONT_SCALE) * self._line_scale