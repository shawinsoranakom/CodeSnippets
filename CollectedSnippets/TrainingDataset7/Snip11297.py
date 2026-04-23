def check(self, **kwargs):
        return [
            *super().check(**kwargs),
            *self._check_image_library_installed(),
        ]