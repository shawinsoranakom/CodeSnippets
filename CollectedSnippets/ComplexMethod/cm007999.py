def search_locations(self, fullname):
        candidate_locations = itertools.chain.from_iterable(
            default_plugin_paths() if candidate == 'default' else candidate_plugin_paths(candidate)
            for candidate in plugin_dirs.value
        )

        parts = Path(*fullname.split('.'))
        for path in orderedSet(candidate_locations, lazy=True):
            candidate = path / parts
            try:
                if candidate.is_dir():
                    yield candidate
                elif path.suffix in ('.zip', '.egg', '.whl') and path.is_file():
                    if parts in dirs_in_zip(path):
                        yield candidate
            except PermissionError as e:
                write_string(f'Permission error while accessing modules in "{e.filename}"\n')