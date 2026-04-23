def test_get_and_head(self):
        """
        Test a view which supplies a GET method also responds correctly to
        HEAD.
        """
        self._assert_simple(SimpleView.as_view()(self.rf.get("/")))
        response = SimpleView.as_view()(self.rf.head("/"))
        self.assertEqual(response.status_code, 200)