def test_template_encoding(self):
        """
        The template is loaded directly, not via a template loader, and should
        be opened as utf-8 charset as is the default specified on template
        engines.
        """
        from django.views.i18n import Path

        view = JavaScriptCatalog.as_view()
        request = RequestFactory().get("/")
        with mock.patch.object(Path, "open") as m:
            view(request)
            m.assert_called_once_with(encoding="utf-8")