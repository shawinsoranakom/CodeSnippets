def target_filename(self, to_path, name):
        target_path = os.path.abspath(to_path)
        filename = os.path.abspath(os.path.join(target_path, name))
        try:
            if os.path.commonpath([target_path, filename]) != target_path:
                raise SuspiciousOperation("Archive contains invalid path: '%s'" % name)
        except ValueError:
            # Different drives on Windows raises ValueError.
            raise SuspiciousOperation("Archive contains invalid path: '%s'" % name)
        return filename