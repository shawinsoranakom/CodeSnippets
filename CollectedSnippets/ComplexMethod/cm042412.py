def _update_text(self, text):
    self._emojis = []
    self._text_size = []
    text = _resolve_value(text)

    if self._elide_right:
      display_text = text

      # Elide text to fit within the rectangle
      text_size = measure_text_cached(self._font, text, self._font_size)
      content_width = self._rect.width - self._text_padding * 2
      if self._icon:
        content_width -= self._icon.width + ICON_PADDING
      if text_size.x > content_width:
        _ellipsis = "..."
        left, right = 0, len(text)
        while left < right:
          mid = (left + right) // 2
          candidate = text[:mid] + _ellipsis
          candidate_size = measure_text_cached(self._font, candidate, self._font_size)
          if candidate_size.x <= content_width:
            left = mid + 1
          else:
            right = mid
        display_text = text[: left - 1] + _ellipsis if left > 0 else _ellipsis

      self._text_wrapped = [display_text]
    else:
      self._text_wrapped = wrap_text(self._font, text, self._font_size, round(self._rect.width - (self._text_padding * 2)))

    for t in self._text_wrapped:
      self._emojis.append(find_emoji(t))
      self._text_size.append(measure_text_cached(self._font, t, self._font_size))