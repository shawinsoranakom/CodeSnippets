def test_sync_decorated_middleware(self):
        response = self.client.get("/middleware_exceptions/view/")
        self.assertEqual(response.status_code, 402)