def __init__(
        self,
        location=None,
        base_url=None,
        file_permissions_mode=None,
        directory_permissions_mode=None,
        allow_overwrite=False,
    ):
        self._location = location
        self._base_url = base_url
        self._file_permissions_mode = file_permissions_mode
        self._directory_permissions_mode = directory_permissions_mode
        self._allow_overwrite = allow_overwrite
        setting_changed.connect(self._clear_cached_properties)