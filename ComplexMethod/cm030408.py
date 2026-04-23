def runTests(self):
        if self.catchbreak:
            installHandler()
        if self.testRunner is None:
            self.testRunner = runner.TextTestRunner
        if isinstance(self.testRunner, type):
            try:
                try:
                    testRunner = self.testRunner(verbosity=self.verbosity,
                                                 failfast=self.failfast,
                                                 buffer=self.buffer,
                                                 warnings=self.warnings,
                                                 tb_locals=self.tb_locals,
                                                 durations=self.durations)
                except TypeError:
                    # didn't accept the tb_locals or durations argument
                    testRunner = self.testRunner(verbosity=self.verbosity,
                                                 failfast=self.failfast,
                                                 buffer=self.buffer,
                                                 warnings=self.warnings)
            except TypeError:
                # didn't accept the verbosity, buffer or failfast arguments
                testRunner = self.testRunner()
        else:
            # it is assumed to be a TestRunner instance
            testRunner = self.testRunner
        self.result = testRunner.run(self.test)
        if self.exit:
            if not self.result.wasSuccessful():
                sys.exit(1)
            elif self.result.testsRun == 0 and len(self.result.skipped) == 0:
                sys.exit(_NO_TESTS_EXITCODE)
            else:
                sys.exit(0)