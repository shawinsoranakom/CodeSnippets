def _get_widget_id(self, k: str) -> str:
        """Turns a value that might be a widget id or a user provided key into
        an appropriate widget id.
        """
        return self._key_id_mapping.get(k, k)