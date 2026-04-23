def _assert_skipping(self, func, expected_exc, msg=None):
        try:
            if msg is not None:
                with self.assertRaisesMessage(expected_exc, msg):
                    func()
            else:
                with self.assertRaises(expected_exc):
                    func()
        except unittest.SkipTest:
            self.fail("%s should not result in a skipped test." % func.__name__)