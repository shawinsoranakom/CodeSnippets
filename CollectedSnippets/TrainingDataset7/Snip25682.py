def test_page_not_found_raised(self):
        self.assertLogsRequest(
            url="/does_not_exist_raised/",
            level="WARNING",
            status_code=404,
            msg="Not Found: /does_not_exist_raised/",
        )