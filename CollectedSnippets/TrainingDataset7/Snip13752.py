def addSubTest(self, test, subtest, err):
        # Follow Python's implementation of unittest.TestResult.addSubTest() by
        # not doing anything when a subtest is successful.
        if err is not None:
            # Call check_picklable() before check_subtest_picklable() since
            # check_picklable() performs the tblib check.
            self.check_picklable(test, err)
            self.check_subtest_picklable(test, subtest)
            self.events.append(("addSubTest", self.test_index, subtest, err))
        super().addSubTest(test, subtest, err)