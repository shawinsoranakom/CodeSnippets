def test_redirect_no_warning(self):
        self.client.get("/redirect/")
        self.assertEqual(self.logger_output.getvalue(), "")