def test_widget_attrs_accept_specified(self):
        f = ImageField(widget=FileInput(attrs={"accept": "image/png"}))
        self.assertEqual(f.widget_attrs(f.widget), {})
        self.assertWidgetRendersTo(
            f, '<input type="file" name="f" accept="image/png" required id="id_f" />'
        )