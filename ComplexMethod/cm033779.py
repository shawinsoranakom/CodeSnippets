def find_executable(executable, cwd=None, path=None):
    """Finds the full path to the executable specified"""
    match = None
    real_cwd = os.getcwd()

    if not cwd:
        cwd = real_cwd

    if os.path.dirname(executable):
        target = os.path.join(cwd, executable)
        if os.path.exists(target) and os.access(target, os.F_OK | os.X_OK):
            match = executable
    else:
        path = os.environ.get('PATH', os.path.defpath)

        path_dirs = path.split(os.path.pathsep)
        seen_dirs = set()

        for path_dir in path_dirs:
            if path_dir in seen_dirs:
                continue

            seen_dirs.add(path_dir)

            if os.path.abspath(path_dir) == real_cwd:
                path_dir = cwd

            candidate = os.path.join(path_dir, executable)

            if os.path.exists(candidate) and os.access(candidate, os.F_OK | os.X_OK):
                match = candidate
                break

    return match