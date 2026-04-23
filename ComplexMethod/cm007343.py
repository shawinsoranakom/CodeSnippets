def compat_get_terminal_size(fallback=(80, 24)):
        from .utils import process_communicate_or_kill
        columns = compat_getenv('COLUMNS')
        if columns:
            columns = int(columns)
        else:
            columns = None
        lines = compat_getenv('LINES')
        if lines:
            lines = int(lines)
        else:
            lines = None

        if columns is None or lines is None or columns <= 0 or lines <= 0:
            try:
                sp = subprocess.Popen(
                    ['stty', 'size'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = process_communicate_or_kill(sp)
                _lines, _columns = map(int, out.split())
            except Exception:
                _columns, _lines = _terminal_size(*fallback)

            if columns is None or columns <= 0:
                columns = _columns
            if lines is None or lines <= 0:
                lines = _lines

        return _terminal_size(columns, lines)