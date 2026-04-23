def addSkip(self, test, reason):
        self.events.append(("addSkip", self.test_index, reason))
        super().addSkip(test, reason)