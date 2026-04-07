async def test_async_middleware_async(self):
        with self.assertLogs("django.request", "WARNING") as cm:
            response = await self.async_client.get("/middleware_exceptions/view/")
        self.assertEqual(response.status_code, 402)
        self.assertEqual(
            cm.records[0].getMessage(),
            "Payment Required: /middleware_exceptions/view/",
        )