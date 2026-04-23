def find_command(cmd, path=None, pathext=None):
    if path is None:
        path = os.environ.get("PATH", "").split(os.pathsep)
    if isinstance(path, str):
        path = [path]
    # check if there are funny path extensions for executables, e.g. Windows
    if pathext is None:
        pathext = os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(os.pathsep)
    # don't use extensions if the command ends with one of them
    for ext in pathext:
        if cmd.endswith(ext):
            pathext = [""]
            break
    # check if we find the command on PATH
    for p in path:
        f = os.path.join(p, cmd)
        if os.path.isfile(f):
            return f
        for ext in pathext:
            fext = f + ext
            if os.path.isfile(fext):
                return fext
    return None