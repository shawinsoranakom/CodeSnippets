async def test_sync_middleware_async(self):
        with self.assertLogs("django.request", "DEBUG") as cm:
            response = await self.async_client.get("/middleware_exceptions/view/")
        self.assertEqual(response.status_code, 402)
        self.assertEqual(
            cm.records[0].getMessage(),
            "Asynchronous handler adapted for middleware "
            "middleware_exceptions.middleware.PaymentMiddleware.",
        )