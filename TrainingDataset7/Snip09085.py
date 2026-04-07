def get_environ(self):
        # Strip all headers with underscores in the name before constructing
        # the WSGI environ. This prevents header-spoofing based on ambiguity
        # between underscores and dashes both normalized to underscores in WSGI
        # env vars. Nginx and Apache 2.4+ both do this as well.
        for k in self.headers:
            if "_" in k:
                del self.headers[k]

        return super().get_environ()