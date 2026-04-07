def directory_permissions_mode(self):
        return self._value_or_setting(
            self._directory_permissions_mode, settings.FILE_UPLOAD_DIRECTORY_PERMISSIONS
        )