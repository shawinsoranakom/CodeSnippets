def _update_text_cache(self, available_width: int):
    """Update cached text processing data."""
    text = self.text

    # Check if cache is still valid
    if (self._cached_text == text and
        self._cached_width == available_width and
        self._cached_wrapped_lines):
      return

    self._cached_text = text
    self._cached_width = available_width

    # Determine wrapping width
    content_width = available_width - (self._text_padding * 2)
    if content_width <= 0:
      content_width = 1

    # Wrap text if enabled
    if self._wrap_text:
      self._cached_wrapped_lines = wrap_text(self._font, text, self._font_size, content_width, self._spacing_pixels)
    else:
      # Split by newlines but don't wrap
      self._cached_wrapped_lines = text.split('\n') if text else [""]

    # Elide lines if needed (for width constraint)
    self._cached_wrapped_lines = [self._elide_line(line, content_width) for line in self._cached_wrapped_lines]

    if self._scroll:
      self._cached_wrapped_lines = self._cached_wrapped_lines[:1]  # Only first line for scrolling

    # Process each line: measure and find emojis
    self._cached_line_sizes = []
    self._cached_line_emojis = []

    for line in self._cached_wrapped_lines:
      emojis = find_emoji(line)
      self._cached_line_emojis.append(emojis)
      # Empty lines should still have height (use font size as line height)
      if not line:
        size = rl.Vector2(0, self._font_size * FONT_SCALE)
      else:
        size = measure_text_cached(self._font, line, self._font_size, self._spacing_pixels)

      # This is the only line
      if self._scroll:
        self._needs_scroll = size.x > content_width

      self._cached_line_sizes.append(size)

    # Calculate total height
    # Each line contributes its measured height * line_height (matching Label's behavior)
    # This includes spacing to the next line
    if self._cached_line_sizes:
      # Match the rendering logic: first line doesn't get line_height scaling
      total_height = 0.0
      for idx, size in enumerate(self._cached_line_sizes):
        if idx == 0:
          total_height += size.y
        else:
          total_height += size.y * self._line_height
      self._cached_total_height = total_height
    else:
      self._cached_total_height = 0.0