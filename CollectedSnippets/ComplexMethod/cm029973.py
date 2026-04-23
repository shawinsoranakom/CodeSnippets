def __init__(self, path):
        if not isinstance(path, str):
            raise TypeError(f"expected str, not {type(path)!r}")
        if not path:
            raise ZipImportError('archive path is empty', path=path)
        if alt_path_sep:
            path = path.replace(alt_path_sep, path_sep)

        prefix = []
        while True:
            try:
                st = _bootstrap_external._path_stat(path)
            except (OSError, ValueError):
                # On Windows a ValueError is raised for too long paths.
                # Back up one path element.
                dirname, basename = _bootstrap_external._path_split(path)
                if dirname == path:
                    raise ZipImportError('not a Zip file', path=path)
                path = dirname
                prefix.append(basename)
            else:
                # it exists
                if (st.st_mode & 0o170000) != 0o100000:  # stat.S_ISREG
                    # it's a not file
                    raise ZipImportError('not a Zip file', path=path)
                break

        if path not in _zip_directory_cache:
            _zip_directory_cache[path] = _read_directory(path)
        self.archive = path
        # a prefix directory following the ZIP file path.
        self.prefix = _bootstrap_external._path_join(*prefix[::-1])
        if self.prefix:
            self.prefix += path_sep