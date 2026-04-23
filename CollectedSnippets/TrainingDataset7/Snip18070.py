def test_public_paths(self):
        paths = ["public_view", "public_function_view"]
        for path in paths:
            response = self.client.get(f"/{path}/")
            self.assertEqual(response.status_code, 200)