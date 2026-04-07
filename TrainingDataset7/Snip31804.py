def test_app(environ, start_response):
            """A WSGI app that returns a hello world."""
            start_response("200 OK", [])
            return [hello_world_body]