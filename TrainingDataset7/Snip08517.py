def __init__(
        self,
        location=None,
        base_url=None,
        file_permissions_mode=None,
        directory_permissions_mode=None,
    ):
        self._location = location
        self._base_url = base_url
        self._file_permissions_mode = file_permissions_mode
        self._directory_permissions_mode = directory_permissions_mode
        self._root = InMemoryDirNode()
        self._resolve(
            self.base_location, create_if_missing=True, leaf_cls=InMemoryDirNode
        )
        setting_changed.connect(self._clear_cached_properties)