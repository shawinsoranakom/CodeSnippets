def _render(self, _):
    """Render the label."""
    if self._rect.width <= 0 or self._rect.height <= 0:
      return

    # Determine available width
    available_width = self._rect.width
    if self._max_width is not None:
      available_width = min(available_width, self._max_width)

    # Update text cache
    self._update_text_cache(int(available_width))

    if not self._cached_wrapped_lines:
      return

    # Calculate which lines fit in the available height
    visible_lines: list[str] = []
    visible_sizes: list[rl.Vector2] = []
    visible_emojis: list[list[tuple[int, int, str]]] = []

    current_height = 0.0
    broke_early = False
    for line, size, emojis in zip(
      self._cached_wrapped_lines,
      self._cached_line_sizes,
      self._cached_line_emojis,
      strict=True):

      # Calculate height needed for this line
      # Each line contributes its height * line_height (matching Label's behavior)
      line_height_needed = size.y * self._line_height

      # Check if this line fits
      if current_height + line_height_needed > self._rect.height:
        # This line doesn't fit
        if len(visible_lines) == 0:
          # First line doesn't fit by height - still show it (will be clipped by scissor if needed)
          # Continue to add this line below
          pass
        else:
          # We have visible lines and this one doesn't fit - mark that we broke early
          broke_early = True
          break

      visible_lines.append(line)
      visible_sizes.append(size)
      visible_emojis.append(emojis)

      current_height += line_height_needed

    # If we broke early (there are more lines that don't fit) and elide is enabled, elide the last visible line
    if broke_early and len(visible_lines) > 0 and self._elide:
      content_width = int(available_width - (self._text_padding * 2))
      if content_width <= 0:
        content_width = 1

      last_line_idx = len(visible_lines) - 1
      last_line = visible_lines[last_line_idx]
      # Force elide the last line to show "..." even if it fits in width (to indicate more content)
      elided = self._elide_line(last_line, content_width, force=True)
      visible_lines[last_line_idx] = elided
      visible_sizes[last_line_idx] = measure_text_cached(self._font, elided, self._font_size, self._spacing_pixels)

    if not visible_lines:
      return

    # Calculate total visible text block height
    # First line is not changed by line_height scaling
    total_visible_height = 0.0
    for idx, size in enumerate(visible_sizes):
      if idx == 0:
        total_visible_height += size.y
      else:
        total_visible_height += size.y * self._line_height

    # Calculate vertical alignment offset
    if self._alignment_vertical == rl.GuiTextAlignmentVertical.TEXT_ALIGN_TOP:
      start_y = self._rect.y
    elif self._alignment_vertical == rl.GuiTextAlignmentVertical.TEXT_ALIGN_BOTTOM:
      start_y = self._rect.y + self._rect.height - total_visible_height
    else:  # TEXT_ALIGN_MIDDLE
      start_y = self._rect.y + (self._rect.height - total_visible_height) / 2

    # Only scissor when we know there is a single scrolling line
    # Pad a little since descenders like g or j may overflow below rect from font_scale
    if self._needs_scroll:
      rl.begin_scissor_mode(int(self._rect.x), int(self._rect.y - self._font_size / 2), int(self._rect.width), int(self._rect.height + self._font_size))

    # Render each line
    current_y = start_y
    for idx, (line, size, emojis) in enumerate(zip(visible_lines, visible_sizes, visible_emojis, strict=True)):
      if self._needs_scroll:
        if self._scroll_state == ScrollState.STARTING:
          if self._scroll_pause_t is None:
            self._scroll_pause_t = rl.get_time() + 2.0
          if rl.get_time() >= self._scroll_pause_t:
            self._scroll_state = ScrollState.SCROLLING
            self._scroll_pause_t = None

        elif self._scroll_state == ScrollState.SCROLLING:
          self._scroll_offset -= 0.8 / 60. * gui_app.target_fps
          # don't fully hide
          if self._scroll_offset <= -size.x - self._rect.width / 3:
            self._scroll_offset = 0
            self._scroll_state = ScrollState.STARTING
            self._scroll_pause_t = None
      else:
        self.reset_scroll()

      self._render_line(line, size, emojis, current_y)

      # Draw 2nd instance for scrolling
      if self._needs_scroll and self._scroll_state != ScrollState.STARTING:
        text2_scroll_offset = size.x + self._rect.width / 3
        self._render_line(line, size, emojis, current_y, text2_scroll_offset)

      # Move to next line (if not last line)
      if idx < len(visible_lines) - 1:
        # Use current line's height * line_height for spacing to next line
        current_y += size.y * self._line_height

    if self._needs_scroll:
      # draw black fade on left and right
      fade_width = 20
      rl.draw_rectangle_gradient_h(int(self._rect.x + self._rect.width - fade_width), int(self._rect.y), fade_width, int(self._rect.height), rl.BLANK, rl.BLACK)

      # stop drawing left fade once text scrolls past
      text_width = visible_sizes[0].x if visible_sizes else 0
      first_copy_in_view = self._scroll_offset + text_width > 0
      draw_left_fade = self._scroll_state != ScrollState.STARTING and first_copy_in_view
      if draw_left_fade:
        rl.draw_rectangle_gradient_h(int(self._rect.x), int(self._rect.y), fade_width, int(self._rect.height), rl.BLACK, rl.BLANK)

      rl.end_scissor_mode()