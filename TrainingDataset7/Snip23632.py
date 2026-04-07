def test_options_for_get_view(self):
        """
        A view implementing GET allows GET and HEAD.
        """
        request = self.rf.options("/")
        view = SimpleView.as_view()
        response = view(request)
        self._assert_allows(response, "GET", "HEAD")