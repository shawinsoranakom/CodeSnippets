def _get_terminfo_dirs() -> list[Path]:
    """Get list of directories to search for terminfo files.

    Based on ncurses behavior in:
    - ncurses/tinfo/db_iterator.c:_nc_next_db()
    - ncurses/tinfo/read_entry.c:_nc_read_entry()
    """
    dirs = []

    terminfo = os.environ.get("TERMINFO")
    if terminfo:
        dirs.append(terminfo)

    try:
        home = Path.home()
        dirs.append(str(home / ".terminfo"))
    except RuntimeError:
        pass

    # Check TERMINFO_DIRS
    terminfo_dirs = os.environ.get("TERMINFO_DIRS", "")
    if terminfo_dirs:
        for d in terminfo_dirs.split(":"):
            if d:
                dirs.append(d)

    dirs.extend(
        [
            "/etc/terminfo",
            "/lib/terminfo",
            "/usr/lib/terminfo",
            "/usr/share/terminfo",
            "/usr/share/lib/terminfo",
            "/usr/share/misc/terminfo",
            "/usr/local/lib/terminfo",
            "/usr/local/share/terminfo",
        ]
    )

    return [Path(d) for d in dirs if Path(d).is_dir()]