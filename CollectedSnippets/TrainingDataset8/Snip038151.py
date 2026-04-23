def _reverse_key_wid_map(self) -> Dict[str, str]:
        """Return a mapping of widget_id : widget_key."""
        wid_key_map = {v: k for k, v in self._key_id_mapping.items()}
        return wid_key_map