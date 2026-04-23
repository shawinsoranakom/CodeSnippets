def _find_exe(basename: str) -> str:
    # Check in Python "scripts" path, e.g. for pipx-installed binaries
    binary = os.path.join(
        sysconfig.get_path('scripts'),
        basename + sysconfig.get_config_var('EXE'))
    if os.access(binary, os.F_OK | os.X_OK) and not os.path.isdir(binary):
        return binary

    if os.name != 'nt':
        return basename

    paths: list[str] = []

    # binary dir
    if getattr(sys, 'frozen', False):
        paths.append(os.path.dirname(sys.executable))
    # cwd
    paths.append(os.getcwd())
    # PATH items
    if path := os.environ.get('PATH'):
        paths.extend(filter(None, path.split(os.path.pathsep)))

    pathext = os.environ.get('PATHEXT')
    if pathext is None:
        exts = _FALLBACK_PATHEXT
    else:
        exts = tuple(ext for ext in pathext.split(os.pathsep) if ext)

    visited = []
    for path in map(os.path.realpath, paths):
        normed = os.path.normcase(path)
        if normed in visited:
            continue
        visited.append(normed)

        for ext in exts:
            binary = os.path.join(path, f'{basename}{ext}')
            if os.access(binary, os.F_OK | os.X_OK) and not os.path.isdir(binary):
                return binary

    return basename