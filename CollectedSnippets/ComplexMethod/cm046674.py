def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if tag in _SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return

        if tag in _HEADING_TAGS:
            self._emit("\n\n")

        elif tag == "a":
            self._finish_link()

        elif tag in _INLINE_EMPHASIS:
            self._emit(_INLINE_EMPHASIS[tag])

        elif tag in _BLOCK_TAGS:
            self._emit("\n\n")

        elif tag == "blockquote":
            if self._bq_stack:
                content = "".join(self._bq_stack.pop())
                prefixed = self._prefix_blockquote(content)
                if prefixed:
                    self._emit("\n\n" + prefixed + "\n\n")

        elif tag == "ul":
            if self._list_stack and self._list_stack[-1] == "ul":
                self._list_stack.pop()
            self._emit("\n")

        elif tag == "ol":
            if self._list_stack and self._list_stack[-1] == "ol":
                self._list_stack.pop()
                if self._ol_counter:
                    self._ol_counter.pop()
            self._emit("\n")

        elif tag == "pre":
            raw = "".join(self._pre_parts)
            self._in_pre = False
            block = "```\n" + raw + "\n```"
            self._emit("\n\n" + block + "\n\n")

        elif tag == "code" and not self._in_pre:
            self._in_inline_code = False
            self._emit("`")

        elif tag in ("th", "td"):
            self._finish_cell()

        elif tag == "tr":
            self._finish_cell()
            self._finish_row()

        elif tag == "table":
            # Flush any remaining row (handles omitted </tr>)
            self._finish_cell()
            self._finish_row()
            self._in_table = False
            self._emit("\n")