def test_integerfield_localized(self):
        """
        A localized IntegerField's widget renders to a text input without any
        number input specific attributes.
        """
        f1 = IntegerField(localize=True)
        self.assertWidgetRendersTo(
            f1, '<input id="id_f" name="f" type="text" required>'
        )