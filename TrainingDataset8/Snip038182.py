def __delitem__(self, key: Key) -> None:
        """Delete the value with the given key.

        Raises
        ------
        StreamlitAPIException
            If the key is not a valid SessionState user key.
        """
        key = str(key)
        require_valid_user_key(key)
        del get_session_state()[key]