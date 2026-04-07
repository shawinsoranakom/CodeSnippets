def get_alternative_name(self, file_root, file_ext):
        if self._allow_overwrite:
            return f"{file_root}{file_ext}"
        return super().get_alternative_name(file_root, file_ext)