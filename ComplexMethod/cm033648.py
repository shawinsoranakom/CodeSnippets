def find_executable(executable: str, cwd: t.Optional[str] = None, path: t.Optional[str] = None, required: t.Union[bool, str] = True) -> t.Optional[str]:
    """
    Find the specified executable and return the full path, or None if it could not be found.
    If required is True an exception will be raised if the executable is not found.
    If required is set to 'warning' then a warning will be shown if the executable is not found.
    """
    match = None
    real_cwd = os.getcwd()

    if not cwd:
        cwd = real_cwd

    if os.path.dirname(executable):
        target = os.path.join(cwd, executable)
        if os.path.exists(target) and os.access(target, os.F_OK | os.X_OK):
            match = executable
    else:
        if path is None:
            path = os.environ.get('PATH', os.path.defpath)

        if path:
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

    if not match and required:
        message = 'Required program "%s" not found.' % executable

        if required != 'warning':
            raise ApplicationError(message)

        display.warning(message)

    return match