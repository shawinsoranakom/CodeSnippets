def test_empty_value_display_booleanfield(self):
        model_field = models.BooleanField(null=True)
        display_value = display_for_field(None, model_field, self.empty_value)
        expected = (
            f'<img src="{settings.STATIC_URL}admin/img/icon-unknown.svg" alt="None" />'
        )
        self.assertHTMLEqual(display_value, expected)