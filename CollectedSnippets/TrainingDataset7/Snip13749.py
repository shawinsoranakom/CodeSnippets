def addDuration(self, test, elapsed):
        super().addDuration(test, elapsed)
        self.events.append(("addDuration", self.test_index, elapsed))