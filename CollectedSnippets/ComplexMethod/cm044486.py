def _check_dynamic_linker(lib: str) -> list[str]:
    """ Locate the folders that contain a given library in ldconfig and $LD_LIBRARY_PATH

    Parameters
    ----------
    lib: str The library to locate

    Returns
    -------
    list[str]
        All real existing folders from ldconfig or $LD_LIBRARY_PATH that contain the given lib
    """
    paths: set[str] = set()
    ldconfig = which("ldconfig")
    if ldconfig:
        paths.update({os.path.realpath(os.path.dirname(line.split("=>")[-1].strip()))
                      for line in _lines_from_command([ldconfig, "-p"])
                      if lib in line and "=>" in line})

    if not os.environ.get("LD_LIBRARY_PATH"):
        return list(paths)

    paths.update({os.path.realpath(path)
                  for path in os.environ["LD_LIBRARY_PATH"].split(":")
                  if path and os.path.exists(path)
                  for fname in os.listdir(path)
                  if lib in fname})
    return list(paths)