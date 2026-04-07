def test_kwarg_instance(self):
        custom = CustomRenderer()
        form = Form(renderer=custom)
        self.assertEqual(form.renderer, custom)