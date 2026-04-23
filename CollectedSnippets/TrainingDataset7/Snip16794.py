def test_render_options_required_field(self):
        """Empty option is present if the field isn't required."""
        form = NotRequiredBandForm()
        output = form.as_table()
        self.assertIn(self.empty_option, output)