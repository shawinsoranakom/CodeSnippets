def stopTest(self, test):
        super().stopTest(test)
        self.logger.removeHandler(self.handler)
        if self.showAll:
            self.stream.write(self._read_logger_stream())
            self.stream.writeln(self.separator2)