def wsgi_app_file_wrapper(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/plain")])
    return environ["wsgi.file_wrapper"](BytesIO(b"foo"))