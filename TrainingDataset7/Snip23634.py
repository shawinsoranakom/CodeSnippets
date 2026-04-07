def test_options_for_post_view(self):
        """
        A view implementing POST allows POST.
        """
        request = self.rf.options("/")
        view = PostOnlyView.as_view()
        response = view(request)
        self._assert_allows(response, "POST")