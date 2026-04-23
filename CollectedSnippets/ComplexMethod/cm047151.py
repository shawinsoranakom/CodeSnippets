def run(self, result, debug=False):
        default_tests_run_count = int(os.environ.get('ODOO_TEST_FAILURE_RETRIES', '0')) + 1
        for test in self:
            if result.shouldStop:
                break
            assert isinstance(test, (TestCase))
            odoo.modules.module.current_test = test
            self._tearDownPreviousClass(test, result)
            self._handleClassSetUp(test, result)
            result._previousTestClass = test.__class__

            if not test.__class__._classSetupFailed:
                if not hasattr(test, '_retry') or test._retry:
                    tests_run_count = default_tests_run_count
                else:
                    tests_run_count = 1
                    _logger.info('Auto retry disabled for %s', test)

                for retry in range(tests_run_count):
                    result.had_failure = False  # reset in case of retry without soft_fail
                    if retry:
                        _logger.runbot(f'Retrying a failed test: {test}')
                    if retry < tests_run_count - 1:
                        with warnings.catch_warnings(), \
                                result.soft_fail(), \
                                odoo.tools.misc.lower_logging(25, logging.INFO) as quiet_log:
                            test(result)
                        if not (result.had_failure or quiet_log.had_error_log):
                            break
                        test = test.__class__(test._testMethodName)  # re-create the test to reset its state
                        odoo.modules.module.current_test = test
                    else:  # last try
                        test(result)
                        if not result.wasSuccessful() and default_tests_run_count != 1:
                            _logger.runbot('Disabling auto-retry after a failed test')
                            default_tests_run_count = 1

        self._tearDownPreviousClass(None, result)
        return result