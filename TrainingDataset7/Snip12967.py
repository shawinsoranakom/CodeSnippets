def delete_cookie(self, key, path="/", domain=None, samesite=None):
        # Browsers can ignore the Set-Cookie header if the cookie doesn't use
        # the secure flag and:
        # - the cookie name starts with "__Host-" or "__Secure-", or
        # - the samesite is "none".
        secure = key.startswith(("__Secure-", "__Host-")) or (
            samesite and samesite.lower() == "none"
        )
        self.set_cookie(
            key,
            max_age=0,
            path=path,
            domain=domain,
            secure=secure,
            expires="Thu, 01 Jan 1970 00:00:00 GMT",
            samesite=samesite,
        )