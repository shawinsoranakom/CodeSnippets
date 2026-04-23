def test_options_for_get_and_post_view(self):
        """
        A view implementing GET and POST allows GET, HEAD, and POST.
        """
        request = self.rf.options("/")
        view = SimplePostView.as_view()
        response = view(request)
        self._assert_allows(response, "GET", "HEAD", "POST")