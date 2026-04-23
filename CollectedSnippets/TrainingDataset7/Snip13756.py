def addUnexpectedSuccess(self, test):
        self.events.append(("addUnexpectedSuccess", self.test_index))
        super().addUnexpectedSuccess(test)