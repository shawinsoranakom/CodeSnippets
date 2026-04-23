def test_decorated_testcase_module(self):
        self.assertEqual(FullyDecoratedTranTestCase.__module__, __name__)