def data_types(self):
        _data_types = self._data_types.copy()
        if self.features.has_native_uuid_field:
            _data_types["UUIDField"] = "uuid"
        return _data_types