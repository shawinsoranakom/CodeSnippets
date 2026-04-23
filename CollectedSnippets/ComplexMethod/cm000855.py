def process(self, chunk: str) -> str:
        """Feed a chunk and return the text that is safe to emit now."""
        self._buffer += chunk
        out: list[str] = []
        while self._buffer:
            if self._in_thinking:
                # Search for both the open and close tags to track nesting.
                open_pos = self._buffer.find(self._open_tag)
                close_pos = self._buffer.find(self._close_tag)
                if close_pos == -1:
                    # No closing tag yet.  Consume any complete nested open
                    # tags first so depth stays accurate even when open and
                    # close tags straddle a chunk boundary.
                    if open_pos != -1:
                        self._depth += 1
                        self._buffer = self._buffer[open_pos + len(self._open_tag) :]
                        continue
                    # No complete close or open tag — keep a tail that could
                    # be the start of either tag.
                    keep = max(len(self._open_tag), len(self._close_tag)) - 1
                    self._buffer = self._buffer[-keep:] if keep else ""
                    return "".join(out)
                if open_pos != -1 and open_pos < close_pos:
                    # A nested open tag appears before the close tag — increase
                    # depth and skip past the nested opener.
                    self._depth += 1
                    self._buffer = self._buffer[open_pos + len(self._open_tag) :]
                else:
                    # Close tag is next; decrease depth.
                    self._buffer = self._buffer[close_pos + len(self._close_tag) :]
                    self._depth -= 1
                    if self._depth == 0:
                        self._in_thinking = False
                        self._open_tag = ""
                        self._close_tag = ""
            else:
                start, open_tag, close_tag = self._find_open_tag()
                if start == -1:
                    # No opening tag; emit everything except a tail that
                    # could start a partial opener on the next chunk.
                    safe_end = len(self._buffer)
                    for keep in range(
                        min(_MAX_OPEN_TAG_LEN - 1, len(self._buffer)), 0, -1
                    ):
                        tail = self._buffer[-keep:]
                        if any(o[:keep] == tail for o, _ in _REASONING_TAG_PAIRS):
                            safe_end = len(self._buffer) - keep
                            break
                    out.append(self._buffer[:safe_end])
                    self._buffer = self._buffer[safe_end:]
                    return "".join(out)
                out.append(self._buffer[:start])
                self._buffer = self._buffer[start + len(open_tag) :]
                self._in_thinking = True
                self._open_tag = open_tag
                self._close_tag = close_tag
                self._depth = 1
        return "".join(out)