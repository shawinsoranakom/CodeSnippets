def format_exception_only(self, *, show_group=False, _depth=0, **kwargs):
        """Format the exception part of the traceback.

        The return value is a generator of strings, each ending in a newline.

        Generator yields the exception message.
        For :exc:`SyntaxError` exceptions, it
        also yields (before the exception message)
        several lines that (when printed)
        display detailed information about where the syntax error occurred.
        Following the message, generator also yields
        all the exception's ``__notes__``.

        When *show_group* is ``True``, and the exception is an instance of
        :exc:`BaseExceptionGroup`, the nested exceptions are included as
        well, recursively, with indentation relative to their nesting depth.
        """
        colorize = kwargs.get("colorize", False)
        if colorize:
            theme = _colorize.get_theme(force_color=True).traceback
        else:
            theme = _colorize.get_theme(force_no_color=True).traceback

        indent = 3 * _depth * ' '
        if not self._have_exc_type:
            yield indent + _format_final_exc_line(None, self._str, colorize=colorize)
            return

        stype = self.exc_type_str
        if not self._is_syntax_error:
            if _depth > 0:
                # Nested exceptions needs correct handling of multiline messages.
                formatted = _format_final_exc_line(
                    stype, self._str, insert_final_newline=False, colorize=colorize
                ).split('\n')
                yield from [
                    indent + l + '\n'
                    for l in formatted
                ]
            else:
                yield _format_final_exc_line(stype, self._str, colorize=colorize)
        else:
            yield from [indent + l for l in self._format_syntax_error(stype, colorize=colorize)]

        if (
            isinstance(self.__notes__, collections.abc.Sequence)
            and not isinstance(self.__notes__, (str, bytes))
        ):
            for note in self.__notes__:
                note = _safe_string(note, 'note')
                yield from _format_note(note, indent, theme)
        elif self.__notes__ is not None:
            note = _safe_string(self.__notes__, '__notes__', func=repr)
            yield from _format_note(note, indent, theme)

        if self.exceptions and show_group:
            for ex in self.exceptions:
                yield from ex.format_exception_only(show_group=show_group, _depth=_depth+1, colorize=colorize)