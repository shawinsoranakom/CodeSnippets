def __getitem__(self, key: Key) -> Any:
        """Return the state or widget value with the given key.

        Raises
        ------
        StreamlitAPIException
            If the key is not a valid SessionState user key.
        """
        key = str(key)
        require_valid_user_key(key)
        return get_session_state()[key]