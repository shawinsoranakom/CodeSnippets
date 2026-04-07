def test_head_no_get(self):
        """
        Test a view which supplies no GET method responds to HEAD with HTTP
        405.
        """
        response = PostOnlyView.as_view()(self.rf.head("/"))
        self.assertEqual(response.status_code, 405)