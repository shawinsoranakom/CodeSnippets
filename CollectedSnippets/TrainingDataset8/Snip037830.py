def _get_file_path(self, value_key: str) -> str:
        """Return the path of the disk cache file for the given value."""
        return get_streamlit_file_path(_CACHE_DIR_NAME, f"{self.key}-{value_key}.memo")