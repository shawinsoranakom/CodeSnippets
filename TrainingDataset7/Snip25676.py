def test_page_found_no_warning(self):
        self.client.get("/innocent/")
        self.assertEqual(self.logger_output.getvalue(), "")