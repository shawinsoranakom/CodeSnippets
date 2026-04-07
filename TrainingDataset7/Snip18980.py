def send_headers(self):
        super().send_headers()
        self.headers_written = True