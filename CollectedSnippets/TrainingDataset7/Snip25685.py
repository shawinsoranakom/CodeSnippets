def test_internal_server_error_599(self):
        self.assertLogsRequest(
            url="/internal_server_error/?status=599",
            level="ERROR",
            status_code=599,
            msg="Unknown Status Code: /internal_server_error/",
        )