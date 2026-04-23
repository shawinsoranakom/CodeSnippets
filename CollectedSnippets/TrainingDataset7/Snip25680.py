async def test_async_page_not_found_warning(self):
        with self.assertLogs("django.request", "WARNING") as cm:
            await self.async_client.get("/does_not_exist/")

        self.assertLogRecord(cm, "Not Found: /does_not_exist/", logging.WARNING, 404)