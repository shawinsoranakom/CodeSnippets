def test_template_encoding(self):
        """
        The template is loaded directly, not via a template loader, and should
        be opened as utf-8 charset as is the default specified on template
        engines.
        """
        from django.views.csrf import Path

        with mock.patch.object(Path, "open") as m:
            csrf_failure(mock.MagicMock(), mock.Mock())
            m.assert_called_once_with(encoding="utf-8")