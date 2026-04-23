def _update_state(self):
    if DO_ZOOM:
      if self._scrolling_to[0] is not None or self.scroll_panel.state != ScrollState.STEADY:
        self._zoom_out_t = rl.get_time() + MIN_ZOOM_ANIMATION_TIME
        self._zoom_filter.update(0.85)
      else:
        if self._zoom_out_t is not None:
          if rl.get_time() > self._zoom_out_t:
            self._zoom_filter.update(1.0)
          else:
            self._zoom_filter.update(0.85)

    # Cancel auto-scroll if user starts manually scrolling (unless block_interaction)
    if (self.scroll_panel.state in (ScrollState.PRESSED, ScrollState.MANUAL_SCROLL) and
        self._scrolling_to[0] is not None and not self._scrolling_to[1]):
      self._scrolling_to = None, False

    if self._scrolling_to[0] is not None and len(self._pending_lift) == 0:
      self._scrolling_to_filter.update(self._scrolling_to[0])
      self.scroll_panel.set_offset(self._scrolling_to_filter.x)

      if abs(self._scrolling_to_filter.x - self._scrolling_to[0]) < 1:
        self.scroll_panel.set_offset(self._scrolling_to[0])
        self._scrolling_to = None, False