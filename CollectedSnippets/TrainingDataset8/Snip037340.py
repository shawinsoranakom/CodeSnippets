def _cursor(self) -> Optional[Cursor]:
        """Return our Cursor. This will be None if we're not running in a
        ScriptThread - e.g., if we're running a "bare" script outside of
        Streamlit.
        """
        if self._provided_cursor is None:
            return cursor.get_container_cursor(self._root_container)
        else:
            return self._provided_cursor