def file_permissions_mode(self):
        return self._value_or_setting(
            self._file_permissions_mode, settings.FILE_UPLOAD_PERMISSIONS
        )