def load(self):
        """
        Load the data from the key itself instead of fetching from some
        external data store. Opposite of _get_session_key(), raise BadSignature
        if signature fails.
        """
        try:
            return signing.loads(
                self.session_key,
                serializer=self.serializer,
                # This doesn't handle non-default expiry dates, see #19201
                max_age=self.get_session_cookie_age(),
                salt="django.contrib.sessions.backends.signed_cookies",
            )
        except Exception:
            # BadSignature, ValueError, or unpickling exceptions. If any of
            # these happen, reset the session.
            self.create()
        return {}