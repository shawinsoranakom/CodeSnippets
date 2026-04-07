def test_render_with_status(self):
        response = self.client.get("/render/status/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content, b"FOO.BAR../render/status/\n")