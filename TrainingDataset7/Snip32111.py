def test_render_with_using(self):
        response = self.client.get("/render/using/")
        self.assertEqual(response.content, b"DTL\n")
        response = self.client.get("/render/using/?using=django")
        self.assertEqual(response.content, b"DTL\n")
        response = self.client.get("/render/using/?using=jinja2")
        self.assertEqual(response.content, b"Jinja2\n")