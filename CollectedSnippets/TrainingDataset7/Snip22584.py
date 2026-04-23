def test_floatfield_localized(self):
        """
        A localized FloatField's widget renders to a text input without any
        number input specific attributes.
        """
        f = FloatField(localize=True)
        self.assertWidgetRendersTo(f, '<input id="id_f" name="f" type="text" required>')