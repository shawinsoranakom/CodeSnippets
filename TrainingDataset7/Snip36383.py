def test_format_html_no_params(self):
        msg = "args or kwargs must be provided."
        with self.assertRaisesMessage(TypeError, msg):
            name = "Adam"
            self.assertEqual(format_html(f"<i>{name}</i>"), "<i>Adam</i>")