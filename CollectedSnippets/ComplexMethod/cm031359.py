def get_cached_location(
            self,
            reader: Reader,
            buffer_from_pos: int | None = None,
            *,
            reuse_full: bool = False,
        ) -> tuple[int, int]:
            """Return (buffer_offset, num_reusable_lines) for incremental refresh.

            Three paths:
            - reuse_full (overlay/message-only): reuse all cached lines.
            - buffer_from_pos=None (full rebuild): rewind to common cursor pos.
            - explicit buffer_from_pos: reuse lines before that position.
            """
            if reuse_full:
                if self.line_end_offsets:
                    last_offset = self.line_end_offsets[-1]
                    if last_offset >= len(reader.buffer):
                        return last_offset, len(self.line_end_offsets)
                return 0, 0
            if buffer_from_pos is None:
                buffer_from_pos = min(reader.pos, self.pos)
            num_common_lines = len(self.line_end_offsets)
            while num_common_lines > 0:
                candidate = self.line_end_offsets[num_common_lines - 1]
                if buffer_from_pos > candidate:
                    break
                num_common_lines -= 1
            # Prompt-only leading rows consume no buffer content. Reusing them
            # in isolation causes the next incremental rebuild to emit them a
            # second time.
            while (
                num_common_lines > 0
                and self.layout_rows[num_common_lines - 1].buffer_advance == 0
            ):
                num_common_lines -= 1
            offset = self.line_end_offsets[num_common_lines - 1] if num_common_lines else 0
            return offset, num_common_lines