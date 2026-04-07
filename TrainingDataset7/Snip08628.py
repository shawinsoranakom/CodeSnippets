def COOKIES(self):
        raw_cookie = get_str_from_wsgi(self.environ, "HTTP_COOKIE", "")
        return parse_cookie(raw_cookie)