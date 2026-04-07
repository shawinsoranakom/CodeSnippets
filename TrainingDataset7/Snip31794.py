def close(self):
        # WSGIRequestHandler closes the output file; we need to make this a
        # no-op so we can still read its contents.
        pass