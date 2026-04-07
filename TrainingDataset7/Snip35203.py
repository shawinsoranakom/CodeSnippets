def test_skip_unless_db_feature(self):
        """
        Testing the django.test.skipUnlessDBFeature decorator.
        """

        # Total hack, but it works, just want an attribute that's always true.
        @skipUnlessDBFeature("__class__")
        def test_func():
            raise ValueError

        @skipUnlessDBFeature("notprovided")
        def test_func2():
            raise ValueError

        @skipUnlessDBFeature("__class__", "__class__")
        def test_func3():
            raise ValueError

        @skipUnlessDBFeature("__class__", "notprovided")
        def test_func4():
            raise ValueError

        self._assert_skipping(test_func, ValueError)
        self._assert_skipping(test_func2, AttributeError)
        self._assert_skipping(test_func3, ValueError)
        self._assert_skipping(test_func4, AttributeError)

        class SkipTestCase(SimpleTestCase):
            @skipUnlessDBFeature("missing")
            def test_foo(self):
                pass

        self._assert_skipping(
            SkipTestCase("test_foo").test_foo,
            ValueError,
            "skipUnlessDBFeature cannot be used on test_foo (test_utils.tests."
            "SkippingTestCase.test_skip_unless_db_feature.<locals>.SkipTestCase."
            "test_foo) as SkippingTestCase.test_skip_unless_db_feature.<locals>."
            "SkipTestCase doesn't allow queries against the 'default' database.",
        )