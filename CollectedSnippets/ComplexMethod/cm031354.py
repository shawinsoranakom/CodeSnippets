def calc_screen(self) -> RenderedScreen:
        """Translate the editable buffer into a base rendered screen."""
        num_common_lines = 0
        offset = 0
        if self.last_refresh_cache.valid(self):
            if (
                self.invalidation.buffer_from_pos is None
                and not (
                    self.invalidation.full
                    or self.invalidation.prompt
                    or self.invalidation.layout
                    or self.invalidation.theme
                )
                and (self.invalidation.message or self.invalidation.overlay)
            ):
                # Fast path: only overlays or messages changed.
                offset, num_common_lines = self.last_refresh_cache.get_cached_location(
                    self,
                    reuse_full=True,
                )
                assert not self.last_refresh_cache.line_end_offsets or (
                    self.last_refresh_cache.line_end_offsets[-1] >= len(self.buffer)
                ), "Buffer modified without invalidate_buffer() call"
            else:
                offset, num_common_lines = self.last_refresh_cache.get_cached_location(
                    self,
                    self._buffer_refresh_from_pos(),
                )

        base_render_lines = self.last_refresh_cache.render_lines[:num_common_lines]
        layout_rows = self.last_refresh_cache.layout_rows[:num_common_lines]
        last_refresh_line_end_offsets = self.last_refresh_cache.line_end_offsets[:num_common_lines]

        source_lines = self._build_source_lines(offset, num_common_lines)
        content_lines = self._build_content_lines(
            source_lines,
            prompt_from_cache=bool(offset and self.buffer[offset - 1] != "\n"),
        )
        layout_result = self._layout_content(content_lines, offset)
        base_render_lines.extend(self._render_wrapped_rows(layout_result.wrapped_rows))
        layout_rows.extend(layout_result.layout_map.rows)
        last_refresh_line_end_offsets.extend(layout_result.line_end_offsets)

        self.layout = LayoutMap(tuple(layout_rows))
        self.cxy = self.pos2xy()
        if not source_lines:
            # reuse_full path: _build_source_lines didn't run,
            # so lxy wasn't updated. Derive it from the buffer.
            self.lxy = self._compute_lxy()
        self.last_refresh_cache.update_cache(
            self,
            base_render_lines,
            layout_rows,
            last_refresh_line_end_offsets,
        )
        return RenderedScreen(tuple(base_render_lines), self.cxy)