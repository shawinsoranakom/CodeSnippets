def addError(self, test, err):
        super().addError(test, err)
        self.errors[-1] = self.errors[-1] + (self._read_logger_stream(),)