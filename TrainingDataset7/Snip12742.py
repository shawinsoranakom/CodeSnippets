def path(self):
        """
        Ensure an absolute path.
        Relative paths are resolved via the {% static %} template tag.
        """
        if self._path.startswith(("http://", "https://", "/")):
            return self._path
        return static(self._path)