def get_pager() -> Pager:
    """Decide what method to use for paging through text."""
    if not hasattr(sys.stdin, "isatty"):
        return plain_pager
    if not hasattr(sys.stdout, "isatty"):
        return plain_pager
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return plain_pager
    if sys.platform == "emscripten":
        return plain_pager
    use_pager = os.environ.get('MANPAGER') or os.environ.get('PAGER')
    if use_pager:
        if sys.platform == 'win32': # pipes completely broken in Windows
            return lambda text, title='': tempfile_pager(plain(text), use_pager)
        elif os.environ.get('TERM') in ('dumb', 'emacs'):
            return lambda text, title='': pipe_pager(plain(text), use_pager, title)
        else:
            return lambda text, title='': pipe_pager(text, use_pager, title)
    if os.environ.get('TERM') in ('dumb', 'emacs'):
        return plain_pager
    if sys.platform == 'win32':
        return lambda text, title='': tempfile_pager(plain(text), 'more <')
    if hasattr(os, 'system') and os.system('(pager) 2>/dev/null') == 0:
        return lambda text, title='': pipe_pager(text, 'pager', title)
    if hasattr(os, 'system') and os.system('(less) 2>/dev/null') == 0:
        return lambda text, title='': pipe_pager(text, 'less', title)

    import tempfile
    (fd, filename) = tempfile.mkstemp()
    os.close(fd)
    try:
        if hasattr(os, 'system') and os.system('more "%s"' % filename) == 0:
            return lambda text, title='': pipe_pager(text, 'more', title)
        else:
            return tty_pager
    finally:
        os.unlink(filename)