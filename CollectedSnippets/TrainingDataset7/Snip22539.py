def test_decimalfield_localized(self):
        """
        A localized DecimalField's widget renders to a text input without
        number input specific attributes.
        """
        f = DecimalField(localize=True)
        self.assertWidgetRendersTo(f, '<input id="id_f" name="f" type="text" required>')