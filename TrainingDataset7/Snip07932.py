def is_empty(self):
        "Return True when there is no session_key and the session is empty."
        try:
            return not self._session_key and not self._session_cache
        except AttributeError:
            return True