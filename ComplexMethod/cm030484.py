def _iterencode_list(lst, _current_indent_level):
        if not lst:
            yield '[]'
            return
        if markers is not None:
            markerid = id(lst)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = lst
        buf = '['
        if _indent is not None:
            _current_indent_level += 1
            newline_indent = '\n' + _indent * _current_indent_level
            separator = _item_separator + newline_indent
            buf += newline_indent
        else:
            newline_indent = None
            separator = _item_separator
        for i, value in enumerate(lst):
            if i:
                buf = separator
            try:
                if isinstance(value, str):
                    yield buf + _encoder(value)
                elif value is None:
                    yield buf + 'null'
                elif value is True:
                    yield buf + 'true'
                elif value is False:
                    yield buf + 'false'
                elif isinstance(value, int):
                    # Subclasses of int/float may override __repr__, but we still
                    # want to encode them as integers/floats in JSON. One example
                    # within the standard library is IntEnum.
                    yield buf + int.__repr__(value)
                elif isinstance(value, float):
                    # see comment above for int
                    yield buf + _floatstr(value)
                else:
                    yield buf
                    if isinstance(value, (list, tuple)):
                        chunks = _iterencode_list(value, _current_indent_level)
                    elif isinstance(value, (dict, frozendict)):
                        chunks = _iterencode_dict(value, _current_indent_level)
                    else:
                        chunks = _iterencode(value, _current_indent_level)
                    yield from chunks
            except GeneratorExit:
                raise
            except BaseException as exc:
                exc.add_note(f'when serializing {type(lst).__name__} item {i}')
                raise
        if newline_indent is not None:
            _current_indent_level -= 1
            yield '\n' + _indent * _current_indent_level
        yield ']'
        if markers is not None:
            del markers[markerid]