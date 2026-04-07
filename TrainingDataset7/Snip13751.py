def addFailure(self, test, err):
        self.check_picklable(test, err)
        self.events.append(("addFailure", self.test_index, err))
        super().addFailure(test, err)