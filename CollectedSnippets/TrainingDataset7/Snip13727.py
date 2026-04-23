def startTest(self, test):
        self.handler = logging.StreamHandler(io.StringIO())
        self.handler.setFormatter(QueryFormatter())
        self.logger.addHandler(self.handler)
        super().startTest(test)