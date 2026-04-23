def test_widget_attrs_default_accept(self):
        f = ImageField()
        # Nothing added for non-FileInput widgets.
        self.assertEqual(f.widget_attrs(Widget()), {})
        self.assertEqual(f.widget_attrs(FileInput()), {"accept": "image/*"})
        self.assertEqual(f.widget_attrs(ClearableFileInput()), {"accept": "image/*"})
        self.assertWidgetRendersTo(
            f, '<input type="file" name="f" accept="image/*" required id="id_f" />'
        )