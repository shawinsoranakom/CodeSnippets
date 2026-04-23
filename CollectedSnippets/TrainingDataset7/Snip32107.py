def test_render(self):
        response = self.client.get("/render/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"FOO.BAR../render/\n")
        self.assertEqual(response.headers["Content-Type"], "text/html; charset=utf-8")
        self.assertFalse(hasattr(response.context.request, "current_app"))