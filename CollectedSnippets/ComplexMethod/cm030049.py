def select_wildcard(path, exists=False):
            try:
                entries = self.scandir(path)
            except OSError:
                pass
            else:
                for entry, entry_name, entry_path in entries:
                    if match is None or match(entry_name):
                        if dir_only:
                            try:
                                if not entry.is_dir():
                                    continue
                            except OSError:
                                continue
                            entry_path = self.concat_path(entry_path, self.sep)
                            yield from select_next(entry_path, exists=True)
                        else:
                            yield entry_path