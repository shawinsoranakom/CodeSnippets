def test_app(environ, start_response):
            """A WSGI app that just reflects its HTTP environ."""
            start_response("200 OK", [])
            http_environ_items = sorted(
                "%s:%s" % (k, v) for k, v in environ.items() if k.startswith("HTTP_")
            )
            yield (",".join(http_environ_items)).encode()