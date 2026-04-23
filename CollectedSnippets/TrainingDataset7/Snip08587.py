def COOKIES(self):
        return parse_cookie(self.META.get("HTTP_COOKIE", ""))