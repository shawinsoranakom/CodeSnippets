def _extract_content(self, current_text: str) -> str | None:
        """Return unsent non-tool-call text, or None.

        Collects all text outside ``<tool_call>...</tool_call>`` regions,
        including text between consecutive tool calls.  Holds back any
        suffix that could be a partial ``<tool_call>`` tag.
        """
        # Build the "sendable index" — the furthest point we can send
        # content up to.  We scan through the text collecting segments
        # that are outside tool-call regions.
        content_segments: list[str] = []
        pos = self._sent_content_idx

        while pos < len(current_text):
            start = current_text.find(self.tool_call_start_token, pos)
            if start == -1:
                # No more tool calls — send up to (len - partial-tag overlap)
                tail = current_text[pos:]
                overlap = partial_tag_overlap(tail, self.tool_call_start_token)
                sendable = tail[: len(tail) - overlap] if overlap else tail
                if sendable:
                    content_segments.append(sendable)
                pos = len(current_text) - overlap
                break

            # Text before this <tool_call>
            if start > pos:
                content_segments.append(current_text[pos:start])

            # Skip past the </tool_call> (or to end if incomplete)
            end = current_text.find(self.tool_call_end_token, start)
            if end != -1:
                pos = end + len(self.tool_call_end_token)
            else:
                # Incomplete tool call — nothing more to send
                pos = start
                break

        if content_segments:
            self._sent_content_idx = pos
            return "".join(content_segments)
        # Even if no content, advance past completed tool-call regions
        if pos > self._sent_content_idx:
            self._sent_content_idx = pos
        return None