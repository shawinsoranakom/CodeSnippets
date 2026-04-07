def _get_scheme(self):
        return self.environ.get("wsgi.url_scheme")