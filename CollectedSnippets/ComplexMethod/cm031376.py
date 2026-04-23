def tty_pager(text: str, title: str = '') -> None:
    """Page through text on a text terminal."""
    lines = plain(escape_stdout(text)).split('\n')
    has_tty = False
    try:
        import tty
        import termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        tty.setcbreak(fd)
        has_tty = True

        def getchar() -> str:
            return sys.stdin.read(1)

    except (ImportError, AttributeError, io.UnsupportedOperation):
        def getchar() -> str:
            return sys.stdin.readline()[:-1][:1]

    try:
        try:
            h = int(os.environ.get('LINES', 0))
        except ValueError:
            h = 0
        if h <= 1:
            h = 25
        r = inc = h - 1
        sys.stdout.write('\n'.join(lines[:inc]) + '\n')
        while lines[r:]:
            sys.stdout.write('-- more --')
            sys.stdout.flush()
            c = getchar()

            if c in ('q', 'Q'):
                sys.stdout.write('\r          \r')
                break
            elif c in ('\r', '\n'):
                sys.stdout.write('\r          \r' + lines[r] + '\n')
                r = r + 1
                continue
            if c in ('b', 'B', '\x1b'):
                r = r - inc - inc
                if r < 0: r = 0
            sys.stdout.write('\n' + '\n'.join(lines[r:r+inc]) + '\n')
            r = r + inc

    finally:
        if has_tty:
            termios.tcsetattr(fd, termios.TCSAFLUSH, old)