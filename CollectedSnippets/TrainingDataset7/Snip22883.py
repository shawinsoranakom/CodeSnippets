def test_get_context_errors(self):
        custom = CustomRenderer()
        form = Form(renderer=custom)
        context = form.get_context()
        self.assertEqual(context["errors"].renderer, custom)