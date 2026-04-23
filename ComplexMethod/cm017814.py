def cleanup_headers(self):
        super().cleanup_headers()
        if (
            self.environ["REQUEST_METHOD"] == "HEAD"
            and "Content-Length" in self.headers
            and str(self.headers["Content-Length"]) == "0"
        ):
            del self.headers["Content-Length"]
        # HTTP/1.1 requires support for persistent connections. Send 'close' if
        # the content length is unknown to prevent clients from reusing the
        # connection.
        if (
            self.environ["REQUEST_METHOD"] != "HEAD"
            and "Content-Length" not in self.headers
        ):
            self.headers["Connection"] = "close"
        # Persistent connections require threading server.
        elif not isinstance(self.request_handler.server, socketserver.ThreadingMixIn):
            self.headers["Connection"] = "close"
        # Mark the connection for closing if it's set as such above or if the
        # application sent the header.
        if self.headers.get("Connection") == "close":
            self.request_handler.close_connection = True