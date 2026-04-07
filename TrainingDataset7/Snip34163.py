def test_form_template_reset_template_change(self, mock_renderer):
        template_path = Path(__file__).parent / "templates" / "index.html"
        self.assertIs(autoreload.template_changed(None, template_path), True)
        mock_renderer.assert_called_once()