def test_render_with_content_type(self):
        response = self.client.get("/render/content_type/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"FOO.BAR../render/content_type/\n")
        self.assertEqual(response.headers["Content-Type"], "application/x-rendertest")