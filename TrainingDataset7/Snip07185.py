def __repr__(self):
        m = self._metadata
        version = f"v{m.binary_format_major_version}.{m.binary_format_minor_version}"
        return f"<{self.__class__.__name__} [{version}] _path='{self._path}'>"