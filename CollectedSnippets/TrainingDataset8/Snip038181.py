def __setitem__(self, key: Key, value: Any) -> None:
        """Set the value of the given key.

        Raises
        ------
        StreamlitAPIException
            If the key is not a valid SessionState user key.
        """
        key = str(key)
        require_valid_user_key(key)
        get_session_state()[key] = value