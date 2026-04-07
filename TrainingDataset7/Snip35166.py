def isolate_debug_test(self, test_suite, result):
        # Suite teardown needs to be manually called to isolate failures.
        test_suite._tearDownPreviousClass(None, result)
        test_suite._handleModuleTearDown(result)