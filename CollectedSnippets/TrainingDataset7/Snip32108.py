def test_render_with_multiple_templates(self):
        response = self.client.get("/render/multiple_templates/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"FOO.BAR../render/multiple_templates/\n")