def test_default(self):
        form = Form()
        self.assertEqual(form.renderer, get_default_renderer())