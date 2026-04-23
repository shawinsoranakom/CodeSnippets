def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()

        if tag in _SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return

        attr_dict = dict(attrs)

        if tag in _HEADING_TAGS:
            level = int(tag[1])
            self._emit("\n\n" + "#" * level + " ")

        elif tag == "a":
            self._link_href = attr_dict.get("href")
            self._link_text_parts = []
            self._in_link = True

        elif tag in _INLINE_EMPHASIS:
            self._emit(_INLINE_EMPHASIS[tag])

        elif tag == "br":
            self._emit("\n")

        elif tag in _BLOCK_TAGS:
            self._emit("\n\n")

        elif tag == "hr":
            self._emit("\n\n---\n\n")

        elif tag == "blockquote":
            self._emit("\n\n")
            self._bq_stack.append([])

        elif tag == "ul":
            self._list_stack.append("ul")
            self._emit("\n")

        elif tag == "ol":
            self._list_stack.append("ol")
            start_attr = attr_dict.get("start")
            try:
                start = int(start_attr) if start_attr is not None else 1
            except (ValueError, TypeError):
                start = 1
            self._ol_counter.append(start - 1)
            self._emit("\n")

        elif tag == "li":
            indent = "  " * max(0, len(self._list_stack) - 1)
            if self._list_stack and self._list_stack[-1] == "ol":
                if self._ol_counter:
                    self._ol_counter[-1] += 1
                    self._emit(f"\n{indent}{self._ol_counter[-1]}. ")
                else:
                    self._emit(f"\n{indent}1. ")
            else:
                self._emit(f"\n{indent}* ")

        elif tag == "pre":
            self._pre_parts = []
            self._in_pre = True

        elif tag == "code" and not self._in_pre:
            self._in_inline_code = True
            self._emit("`")

        elif tag == "table":
            self._in_table = True
            self._header_row_done = False
            self._is_first_row = True
            self._emit("\n\n")

        elif tag == "tr":
            # Flush any open cell/row from a previous row that may
            # have omitted its optional </td> or </tr> end tags.
            self._finish_cell()
            self._finish_row()

        elif tag in ("th", "td"):
            # Flush any open cell (handles omitted </td>/<th>)
            self._finish_cell()
            self._cell_parts = []
            self._in_cell = True
            if tag == "th":
                self._row_has_th = True

        elif tag == "img":
            # Skip images -- keeps fetched page text focused on readable
            # content and avoids data-URI amplification.
            return