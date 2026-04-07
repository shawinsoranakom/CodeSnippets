def snapshot_files(self):
        # watched_files may produce duplicate paths if globs overlap.
        seen_files = set()
        for file in self.watched_files():
            if file in seen_files:
                continue
            try:
                mtime = file.stat().st_mtime
            except OSError:
                # This is thrown when the file does not exist.
                continue
            seen_files.add(file)
            yield file, mtime