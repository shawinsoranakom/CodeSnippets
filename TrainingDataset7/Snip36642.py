def test_mark_safe_decorator_does_not_affect_promises(self):
        """
        mark_safe doesn't affect lazy strings (Promise objects).
        """

        def html_str():
            return "<html></html>"

        lazy_str = lazy(html_str, str)()
        self.assertEqual(mark_safe(lazy_str), html_str())