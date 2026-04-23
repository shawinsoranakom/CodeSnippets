def test_decorated_testcase_name(self):
        self.assertEqual(
            FullyDecoratedTranTestCase.__name__, "FullyDecoratedTranTestCase"
        )