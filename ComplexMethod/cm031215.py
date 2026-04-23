def _find_children(self):
        with _os.scandir(self.path) as scan_iterator:
            while True:
                try:
                    entry = next(scan_iterator)
                    if entry.name == _PYCACHE:
                        continue
                    # packages
                    if entry.is_dir() and '.' not in entry.name:
                        yield entry.name
                    # files
                    if entry.is_file():
                        yield from {
                            entry.name.removesuffix(suffix)
                            for suffix, _ in self._loaders
                            if entry.name.endswith(suffix)
                        }
                except OSError:
                    pass  # ignore exceptions from next(scan_iterator) and os.DirEntry
                except StopIteration:
                    break