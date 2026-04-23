def test_resolve_login_required_view(self):
        match = resolve("/template/login_required/")
        self.assertIs(match.func.view_class, TemplateView)