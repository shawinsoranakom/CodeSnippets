def addFailure(self, test, err):
        super().addFailure(test, err)
        self.debug(err)