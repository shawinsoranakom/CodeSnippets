def addFailure(self, test, err):
        super().addFailure(test, err)
        self.failures[-1] = self.failures[-1] + (self._read_logger_stream(),)