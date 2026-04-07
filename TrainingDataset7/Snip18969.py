def send_big_data_app(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/plain")])
    # Return a blob of data that is 1.5 times the maximum chunk size.
    return [b"x" * (MAX_SOCKET_CHUNK_SIZE + MAX_SOCKET_CHUNK_SIZE // 2)]