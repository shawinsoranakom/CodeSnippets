def test_async_middleware(self):
        with self.assertLogs("django.request", "DEBUG") as cm:
            response = self.client.get("/middleware_exceptions/view/")
        self.assertEqual(response.status_code, 402)
        self.assertEqual(
            cm.records[0].getMessage(),
            "Synchronous handler adapted for middleware "
            "middleware_exceptions.middleware.async_payment_middleware.",
        )