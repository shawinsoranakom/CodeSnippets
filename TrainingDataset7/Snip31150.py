def test_view_function_with_args(self):
        self.assertEqual("/params/django/", resolve_url(params_view, "django"))