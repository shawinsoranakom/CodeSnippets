def test_internal_server_error(self):
        self.assertLogsRequest(
            url="/internal_server_error/",
            level="ERROR",
            status_code=500,
            msg="Internal Server Error: /internal_server_error/",
        )