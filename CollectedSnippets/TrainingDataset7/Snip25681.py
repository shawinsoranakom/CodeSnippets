async def test_async_control_chars_escaped(self):
        with self.assertLogs("django.request", "WARNING") as cm:
            await self.async_client.get(r"/%1B[1;31mNOW IN RED!!!1B[0m/")

        self.assertLogRecord(
            cm, r"Not Found: /\x1b[1;31mNOW IN RED!!!1B[0m/", logging.WARNING, 404
        )