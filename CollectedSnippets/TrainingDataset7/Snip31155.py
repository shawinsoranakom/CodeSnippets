def test_lazy_reverse(self):
        """
        Passing the result of reverse_lazy is resolved to a real URL
        string.
        """
        resolved_url = resolve_url(reverse_lazy("some-view"))
        self.assertIsInstance(resolved_url, str)
        self.assertEqual("/some-url/", resolved_url)