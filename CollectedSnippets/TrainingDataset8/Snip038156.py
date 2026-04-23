def __getitem__(self, key: str) -> Any:
        wid_key_map = self._reverse_key_wid_map
        widget_id = self._get_widget_id(key)

        if widget_id in wid_key_map and widget_id == key:
            # the "key" is a raw widget id, so get its associated user key for lookup
            key = wid_key_map[widget_id]
        try:
            return self._getitem(widget_id, key)
        except KeyError:
            raise KeyError(_missing_key_error_message(key))