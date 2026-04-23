def test_log_custom_message(self):
        with self.assertLogs("django.request", "DEBUG") as cm:
            self.client.get("/middleware_exceptions/view/")
        self.assertEqual(
            cm.records[0].getMessage(),
            "MiddlewareNotUsed('middleware_exceptions.tests."
            "MyMiddlewareWithExceptionMessage'): spam eggs",
        )