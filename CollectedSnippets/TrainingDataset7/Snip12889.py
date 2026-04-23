def get_signed_cookie(self, key, default=RAISE_ERROR, salt="", max_age=None):
        """
        Attempt to return a signed cookie. If the signature fails or the
        cookie has expired, raise an exception, unless the `default` argument
        is provided, in which case return that value.
        """
        try:
            cookie_value = self.COOKIES[key]
        except KeyError:
            if default is not RAISE_ERROR:
                return default
            else:
                raise
        try:
            value = signing.get_cookie_signer(salt=key + salt).unsign(
                cookie_value, max_age=max_age
            )
        except signing.BadSignature:
            if default is not RAISE_ERROR:
                return default
            else:
                raise
        return value