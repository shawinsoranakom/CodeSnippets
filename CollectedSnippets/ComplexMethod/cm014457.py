def get_file_pathnames_from_root(
    root: str,
    masks: str | list[str],
    recursive: bool = False,
    abspath: bool = False,
    non_deterministic: bool = False,
) -> Iterable[str]:
    # print out an error message and raise the error out
    def onerror(err: OSError) -> NoReturn:
        warnings.warn(err.filename + " : " + err.strerror, stacklevel=2)
        raise err

    if os.path.isfile(root):
        path = root
        if abspath:
            path = os.path.abspath(path)
        fname = os.path.basename(path)
        if match_masks(fname, masks):
            yield path
    else:
        for path, dirs, files in os.walk(root, onerror=onerror):
            if abspath:
                path = os.path.abspath(path)
            if not non_deterministic:
                files.sort()
            for f in files:
                if match_masks(f, masks):
                    yield os.path.join(path, f)
            if not recursive:
                break
            if not non_deterministic:
                # Note that this is in-place modifying the internal list from `os.walk`
                # This only works because `os.walk` doesn't shallow copy before turn
                # https://github.com/python/cpython/blob/f4c03484da59049eb62a9bf7777b963e2267d187/Lib/os.py#L407
                dirs.sort()