def test_view_function(self):
        """
        Passing a view function to resolve_url() results in the URL path
        mapping to that view name.
        """
        resolved_url = resolve_url(some_view)
        self.assertEqual("/some-url/", resolved_url)