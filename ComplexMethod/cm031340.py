def do(self) -> None:
        r: ReadlineAlikeReader
        r = self.reader  # type: ignore[assignment]
        r.invalidate_overlay()  # hide completion menu, if visible

        # if there are already several lines and the cursor
        # is not on the last one, always insert a new \n.
        text = r.get_unicode()

        if "\n" in r.buffer[r.pos :] or (
            r.more_lines is not None and r.more_lines(text)
        ):
            def _newline_before_pos():
                before_idx = r.pos - 1
                while before_idx > 0 and text[before_idx].isspace():
                    before_idx -= 1
                return text[before_idx : r.pos].count("\n") > 0

            # if there's already a new line before the cursor then
            # even if the cursor is followed by whitespace, we assume
            # the user is trying to terminate the block
            if _newline_before_pos() and text[r.pos:].isspace():
                self.finish = True
                return

            # auto-indent the next line like the previous line
            prevlinestart, indent = _get_previous_line_indent(r.buffer, r.pos)
            r.insert("\n")
            if not self.reader.paste_mode:
                if indent:
                    for i in range(prevlinestart, prevlinestart + indent):
                        r.insert(r.buffer[i])
                r.update_last_used_indentation()
                if _should_auto_indent(r.buffer, r.pos):
                    if r.last_used_indentation is not None:
                        indentation = r.last_used_indentation
                    else:
                        # default
                        indentation = " " * 4
                    r.insert(indentation)
        elif not self.reader.paste_mode:
            self.finish = True
        else:
            r.insert("\n")