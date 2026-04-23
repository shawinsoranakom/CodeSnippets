def make_test_suite(self, suite=None, suite_class=None):
        class Tests1(unittest.TestCase):
            def test1(self):
                pass

            def test2(self):
                pass

        class Tests2(unittest.TestCase):
            def test1(self):
                pass

            def test2(self):
                pass

        return self.build_test_suite(
            (Tests1, Tests2),
            suite=suite,
            suite_class=suite_class,
        )