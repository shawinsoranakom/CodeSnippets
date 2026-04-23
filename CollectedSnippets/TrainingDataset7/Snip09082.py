def finish_response(self):
        if self.environ["REQUEST_METHOD"] == "HEAD":
            try:
                deque(self.result, maxlen=0)  # Consume iterator.
                # Don't call self.finish_content() as, if the headers have not
                # been sent and Content-Length isn't set, it'll default to "0"
                # which will prevent omission of the Content-Length header with
                # HEAD requests as permitted by RFC 9110 Section 9.3.2.
                # Instead, send the headers, if not sent yet.
                if not self.headers_sent:
                    self.send_headers()
            finally:
                self.close()
        else:
            super().finish_response()