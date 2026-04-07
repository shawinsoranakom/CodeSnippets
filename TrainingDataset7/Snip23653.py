def test_resolve_view(self):
        match = resolve("/template/content_type/")
        self.assertIs(match.func.view_class, TemplateView)
        self.assertEqual(match.func.view_initkwargs["content_type"], "text/plain")