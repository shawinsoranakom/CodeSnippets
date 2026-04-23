def test_permission_denied(self):
        self.assertLogsRequest(
            url="/permission_denied/",
            level="WARNING",
            status_code=403,
            msg="Forbidden (Permission denied): /permission_denied/",
            exc_class=PermissionDenied,
        )