def _format_syntax_error(self, stype, **kwargs):
        """Format SyntaxError exceptions (internal helper)."""
        # Show exactly where the problem was found.
        colorize = kwargs.get("colorize", False)
        if colorize:
            theme = _colorize.get_theme(force_color=True).traceback
        else:
            theme = _colorize.get_theme(force_no_color=True).traceback
        filename_suffix = ''
        if self.lineno is not None:
            yield '  File {}"{}"{}, line {}{}{}\n'.format(
                theme.filename,
                self.filename or "<string>",
                theme.reset,
                theme.line_no,
                self.lineno,
                theme.reset,
                )
        elif self.filename is not None:
            filename_suffix = ' ({})'.format(self.filename)

        text = self.text
        if isinstance(text, str):
            # text  = "   foo\n"
            # rtext = "   foo"
            # ltext =    "foo"
            with suppress(Exception):
                self._find_keyword_typos()
            text = self.text
            rtext = text.rstrip('\n')
            ltext = rtext.lstrip(' \n\f')
            spaces = len(rtext) - len(ltext)
            if self.offset is None:
                yield '    {}\n'.format(ltext)
            elif isinstance(self.offset, int):
                offset = self.offset
                if self.lineno == self.end_lineno:
                    end_offset = (
                        self.end_offset
                        if (
                            isinstance(self.end_offset, int)
                            and self.end_offset != 0
                        )
                        else offset
                    )
                else:
                    end_offset = len(rtext) + 1

                if self.text and offset > len(self.text):
                    offset = len(rtext) + 1
                if self.text and end_offset > len(self.text):
                    end_offset = len(rtext) + 1
                if offset >= end_offset or end_offset < 0:
                    end_offset = offset + 1

                # Convert 1-based column offset to 0-based index into stripped text
                colno = offset - 1 - spaces
                end_colno = end_offset - 1 - spaces
                if colno >= 0:
                    # Calculate display width to account for wide characters
                    dp_colno = _display_width(ltext, colno)
                    highlighted = ltext[colno:end_colno]
                    caret_count = _display_width(highlighted) if highlighted else (end_colno - colno)
                    start_color = end_color = ""
                    if colorize:
                        # colorize from colno to end_colno
                        ltext = (
                            ltext[:colno] +
                            theme.error_highlight + ltext[colno:end_colno] + theme.reset +
                            ltext[end_colno:]
                        )
                        start_color = theme.error_highlight
                        end_color = theme.reset
                    yield '    {}\n'.format(ltext)
                    yield '    {}{}{}{}\n'.format(
                        ' ' * dp_colno,
                        start_color,
                        '^' * caret_count,
                        end_color,
                    )
                else:
                    yield '    {}\n'.format(ltext)
        msg = self.msg or "<no detail available>"
        yield "{}{}{}: {}{}{}{}\n".format(
            theme.type,
            stype,
            theme.reset,
            theme.message,
            msg,
            theme.reset,
            filename_suffix,
        )