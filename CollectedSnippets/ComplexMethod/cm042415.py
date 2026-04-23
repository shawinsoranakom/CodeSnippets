def _elide_line(self, line: str, max_width: int, force: bool = False) -> str:
    """Elide a single line if it exceeds max_width. If force is True, always elide even if it fits."""
    if not self._elide and not force:
      return line

    text_size = measure_text_cached(self._font, line, self._font_size, self._spacing_pixels)
    if text_size.x <= max_width and not force:
      return line

    ellipsis = "..."
    # If force=True and line fits, just append ellipsis without truncating
    if force and text_size.x <= max_width:
      ellipsis_size = measure_text_cached(self._font, ellipsis, self._font_size, self._spacing_pixels)
      if text_size.x + ellipsis_size.x <= max_width:
        return line + ellipsis
      # If line + ellipsis doesn't fit, need to truncate
      # Fall through to binary search below

    left, right = 0, len(line)
    while left < right:
      mid = (left + right) // 2
      candidate = line[:mid] + ellipsis
      candidate_size = measure_text_cached(self._font, candidate, self._font_size, self._spacing_pixels)
      if candidate_size.x <= max_width:
        left = mid + 1
      else:
        right = mid
    return line[:left - 1] + ellipsis if left > 0 else ellipsis