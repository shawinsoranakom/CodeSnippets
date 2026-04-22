def initialize(self, path, default_filename, get_pages):
        self._pages = get_pages()

        super().initialize(path=path, default_filename=default_filename)