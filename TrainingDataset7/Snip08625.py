def GET(self):
        # The WSGI spec says 'QUERY_STRING' may be absent.
        raw_query_string = get_bytes_from_wsgi(self.environ, "QUERY_STRING", "")
        return QueryDict(raw_query_string, encoding=self._encoding)