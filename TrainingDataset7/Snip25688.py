def test_i18n_page_found_no_warning(self):
        self.client.get("/exists/")
        self.client.get("/en/exists/")
        self.assertEqual(self.logger_output.getvalue(), "")