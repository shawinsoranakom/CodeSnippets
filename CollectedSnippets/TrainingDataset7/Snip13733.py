def addError(self, test, err):
        super().addError(test, err)
        self.debug(err)