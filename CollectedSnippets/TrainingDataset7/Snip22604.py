def test_widget_attrs_accept_false(self):
        f = ImageField(widget=FileInput(attrs={"accept": False}))
        self.assertEqual(f.widget_attrs(f.widget), {})
        self.assertWidgetRendersTo(
            f, '<input type="file" name="f" required id="id_f" />'
        )