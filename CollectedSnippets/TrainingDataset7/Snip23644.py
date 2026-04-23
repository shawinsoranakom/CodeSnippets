def test_head(self):
        """
        Test a TemplateView responds correctly to HEAD
        """
        response = AboutTemplateView.as_view()(self.rf.head("/about/"))
        self.assertEqual(response.status_code, 200)