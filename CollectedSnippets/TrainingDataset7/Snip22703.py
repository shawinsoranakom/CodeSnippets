def test_urlfield_widget_max_min_length(self):
        f = URLField(min_length=15, max_length=20)
        self.assertEqual("http://example.com", f.clean("http://example.com"))
        self.assertWidgetRendersTo(
            f,
            '<input id="id_f" type="url" name="f" maxlength="20" '
            'minlength="15" required>',
        )
        msg = "'Ensure this value has at least 15 characters (it has 12).'"
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("http://f.com")
        msg = "'Ensure this value has at most 20 characters (it has 37).'"
        with self.assertRaisesMessage(ValidationError, msg):
            f.clean("http://abcdefghijklmnopqrstuvwxyz.com")