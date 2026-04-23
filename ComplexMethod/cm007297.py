def write_string(s, out=None, encoding=None):
    if out is None:
        out = sys.stderr
    assert isinstance(s, compat_str)

    if sys.platform == 'win32' and encoding is None and hasattr(out, 'fileno'):
        if _windows_write_string(s, out):
            return

    if ('b' in getattr(out, 'mode', '')
            or sys.version_info[0] < 3):  # Python 2 lies about mode of sys.stderr
        byt = s.encode(encoding or preferredencoding(), 'ignore')
        out.write(byt)
    elif hasattr(out, 'buffer'):
        enc = encoding or getattr(out, 'encoding', None) or preferredencoding()
        byt = s.encode(enc, 'ignore')
        out.buffer.write(byt)
    else:
        out.write(s)
    out.flush()