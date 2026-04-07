def test_get_only(self):
        """
        Test a view which only allows GET doesn't allow other methods.
        """
        self._assert_simple(SimpleView.as_view()(self.rf.get("/")))
        self.assertEqual(SimpleView.as_view()(self.rf.post("/")).status_code, 405)
        self.assertEqual(
            SimpleView.as_view()(self.rf.get("/", REQUEST_METHOD="FAKE")).status_code,
            405,
        )