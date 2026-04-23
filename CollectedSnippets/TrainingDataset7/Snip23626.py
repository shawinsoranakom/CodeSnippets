def test_get_and_post(self):
        """
        Test a view which only allows both GET and POST.
        """
        self._assert_simple(SimplePostView.as_view()(self.rf.get("/")))
        self._assert_simple(SimplePostView.as_view()(self.rf.post("/")))
        self.assertEqual(
            SimplePostView.as_view()(
                self.rf.get("/", REQUEST_METHOD="FAKE")
            ).status_code,
            405,
        )