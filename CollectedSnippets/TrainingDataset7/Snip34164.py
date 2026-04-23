def test_form_template_reset_template_change_reset_call(self, mock_loader_reset):
        template_path = Path(__file__).parent / "templates" / "index.html"
        self.assertIs(autoreload.template_changed(None, template_path), True)
        mock_loader_reset.assert_called_once()