def _get_session_key(self):
        """
        Instead of generating a random string, generate a secure url-safe
        base64-encoded string of data as our session key.
        """
        return signing.dumps(
            self._session,
            compress=True,
            salt="django.contrib.sessions.backends.signed_cookies",
            serializer=self.serializer,
        )