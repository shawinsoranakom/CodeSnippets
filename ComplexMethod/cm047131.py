def run(self, result):
        result.startTest(self)

        testMethod = getattr(self, self._testMethodName)

        skip = False
        skip_why = ''
        try:
            skip = self.__class__.__unittest_skip__ or testMethod.__unittest_skip__
            skip_why = self.__class__.__unittest_skip_why__ or testMethod.__unittest_skip_why__ or ''
        except AttributeError:  # testMethod may not have a __unittest_skip__ or __unittest_skip_why__
            pass
        if skip:
            result.addSkip(self, skip_why)
            result.stopTest(self)
            return

        outcome = _Outcome(self, result)
        try:
            self._outcome = outcome
            with outcome.testPartExecutor(self):
                self._callSetUp()
            if outcome.success:
                with outcome.testPartExecutor(self, isTest=True):
                    self._callTestMethod(testMethod)
                with outcome.testPartExecutor(self):
                    self._callTearDown()

            self.doCleanups()
            if outcome.success:
                result.addSuccess(self)
            return result
        finally:
            result.stopTest(self)

            # clear the outcome, no more needed
            self._outcome = None