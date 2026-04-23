def _render(self, rect: rl.Rectangle):
    if self._switching:
      self._handle_switch()

    if not self._ensure_connection():
      self._draw_placeholder(rect)
      return

    # Try to get a new buffer without blocking
    buffer = self.client.recv(timeout_ms=0)
    if buffer:
      self._texture_needs_update = True
      self.frame = buffer
    elif not self.client.is_connected():
      # ensure we clear the displayed frame when the connection is lost
      self.frame = None

    if not self.frame:
      self._draw_placeholder(rect)
      return

    transform = self._calc_frame_matrix(rect)
    src_rect = rl.Rectangle(0, 0, float(self.frame.width), float(self.frame.height))
    # Flip driver camera horizontally
    if self._stream_type == VisionStreamType.VISION_STREAM_DRIVER:
      src_rect.width = -src_rect.width

    # Calculate scale
    scale_x = rect.width * transform[0, 0]  # zx
    scale_y = rect.height * transform[1, 1]  # zy

    # Calculate base position (centered)
    x_offset = rect.x + (rect.width - scale_x) / 2
    y_offset = rect.y + (rect.height - scale_y) / 2

    x_offset += transform[0, 2] * rect.width / 2
    y_offset += transform[1, 2] * rect.height / 2

    dst_rect = rl.Rectangle(x_offset, y_offset, scale_x, scale_y)

    # Render with appropriate method
    if TICI:
      self._render_egl(src_rect, dst_rect)
    else:
      self._render_textures(src_rect, dst_rect)