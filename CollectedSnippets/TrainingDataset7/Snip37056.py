def test_template_encoding(self):
        """
        The template is loaded directly, not via a template loader, and should
        be opened as utf-8 charset as is the default specified on template
        engines.
        """
        from django.views.static import Path

        with mock.patch.object(Path, "open") as m:
            directory_index(mock.MagicMock(), mock.MagicMock())
            m.assert_called_once_with(encoding="utf-8")