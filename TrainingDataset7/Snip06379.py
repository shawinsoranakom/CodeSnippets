def make_token(self, user):
        """
        Return a token that can be used once to do a password reset
        for the given user.
        """
        return self._make_token_with_timestamp(
            user,
            self._num_seconds(self._now()),
            self.secret,
        )