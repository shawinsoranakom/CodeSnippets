def addSuccess(self, test):
        self.events.append(("addSuccess", self.test_index))
        super().addSuccess(test)