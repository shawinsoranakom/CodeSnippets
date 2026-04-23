def __init__(self, file):
        self._archive = self._archive_cls(file)(file)