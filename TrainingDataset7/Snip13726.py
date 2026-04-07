def _read_logger_stream(self):
        if self.handler is None:
            # Error before tests e.g. in setUpTestData().
            sql = ""
        else:
            self.handler.stream.seek(0)
            sql = self.handler.stream.read()
        return sql