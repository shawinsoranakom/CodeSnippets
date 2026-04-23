def test_form_template_reset_non_template_change(self, mock_renderer):
        self.assertIsNone(autoreload.template_changed(None, Path(__file__)))
        mock_renderer.assert_not_called()