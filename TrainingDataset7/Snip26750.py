def test_do_not_log_when_debug_is_false(self):
        with self.assertNoLogs("django.request", "DEBUG"):
            self.client.get("/middleware_exceptions/view/")