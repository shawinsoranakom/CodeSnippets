def test_valid_view_name(self):
        """
        Passing a view name to resolve_url() results in the URL path mapping
        to that view.
        """
        resolved_url = resolve_url("some-view")
        self.assertEqual("/some-url/", resolved_url)