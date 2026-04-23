def addError(self, test, err):
        self.check_picklable(test, err)

        event_occurred_before_first_test = self.test_index == -1
        if event_occurred_before_first_test and isinstance(
            test, unittest.suite._ErrorHolder
        ):
            self.events.append(("addError", self.test_index, test.id(), err))
        else:
            self.events.append(("addError", self.test_index, err))

        super().addError(test, err)