def terminate(self):
        if self.is_ready.is_set():
            if hasattr(self, "httpd"):
                # Stop the WSGI server
                self.httpd.shutdown()
                self.httpd.server_close()
            self.join()