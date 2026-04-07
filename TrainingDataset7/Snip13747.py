def startTest(self, test):
        super().startTest(test)
        self.events.append(("startTest", self.test_index))