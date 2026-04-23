def test_skip_if_db_feature(self):
        """
        Testing the django.test.skipIfDBFeature decorator.
        """

        @skipIfDBFeature("__class__")
        def test_func():
            raise ValueError

        @skipIfDBFeature("notprovided")
        def test_func2():
            raise ValueError

        @skipIfDBFeature("__class__", "__class__")
        def test_func3():
            raise ValueError

        @skipIfDBFeature("__class__", "notprovided")
        def test_func4():
            raise ValueError

        @skipIfDBFeature("notprovided", "notprovided")
        def test_func5():
            raise ValueError

        self._assert_skipping(test_func, unittest.SkipTest)
        self._assert_skipping(test_func2, AttributeError)
        self._assert_skipping(test_func3, unittest.SkipTest)
        self._assert_skipping(test_func4, unittest.SkipTest)
        self._assert_skipping(test_func5, AttributeError)

        class SkipTestCase(SimpleTestCase):
            @skipIfDBFeature("missing")
            def test_foo(self):
                pass

        self._assert_skipping(
            SkipTestCase("test_foo").test_foo,
            ValueError,
            "skipIfDBFeature cannot be used on test_foo (test_utils.tests."
            "SkippingTestCase.test_skip_if_db_feature.<locals>.SkipTestCase.test_foo) "
            "as SkippingTestCase.test_skip_if_db_feature.<locals>.SkipTestCase "
            "doesn't allow queries against the 'default' database.",
        )