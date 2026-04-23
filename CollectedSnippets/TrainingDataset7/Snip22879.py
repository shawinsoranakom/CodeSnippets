def test_kwarg_class(self):
        custom = CustomRenderer()
        form = Form(renderer=custom)
        self.assertEqual(form.renderer, custom)