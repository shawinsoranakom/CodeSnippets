def test_app(environ, start_response):
            """
            A WSGI app that returns a hello world with non-zero Content-Length.
            """
            start_response("200 OK", [("Content-length", str(content_length))])
            return [hello_world_body]