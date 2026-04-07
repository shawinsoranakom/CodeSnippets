def test_i18n_page_not_found_warning(self):
        self.client.get("/this_does_not/")
        self.client.get("/en/nor_this/")
        self.assertEqual(
            self.logger_output.getvalue(),
            "Not Found: /this_does_not/\nNot Found: /en/nor_this/\n",
        )