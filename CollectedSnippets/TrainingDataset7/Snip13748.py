def stopTest(self, test):
        super().stopTest(test)
        self.events.append(("stopTest", self.test_index))