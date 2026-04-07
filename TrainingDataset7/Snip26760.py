def test_async_and_sync_middleware_sync_call(self):
        response = self.client.get("/middleware_exceptions/view/")
        self.assertEqual(response.content, b"OK")
        self.assertEqual(response.status_code, 200)