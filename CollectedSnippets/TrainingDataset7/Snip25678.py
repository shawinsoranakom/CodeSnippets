def test_page_not_found_warning(self):
        self.assertLogsRequest(
            url="/does_not_exist/",
            level="WARNING",
            status_code=404,
            msg="Not Found: /does_not_exist/",
        )