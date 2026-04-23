def check(self, **kwargs):
        return [
            *super().check(**kwargs),
            *self._check_allowing_files_or_folders(**kwargs),
        ]