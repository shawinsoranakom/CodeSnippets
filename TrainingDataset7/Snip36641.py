def test_mark_safe_decorator_does_not_affect_dunder_html(self):
        """
        mark_safe doesn't affect a callable that has an __html__() method.
        """

        class SafeStringContainer:
            def __html__(self):
                return "<html></html>"

        self.assertIs(mark_safe(SafeStringContainer), SafeStringContainer)