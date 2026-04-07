def test_view_function_with_kwargs(self):
        self.assertEqual("/params/django/", resolve_url(params_view, slug="django"))