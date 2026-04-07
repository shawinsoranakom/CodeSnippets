def test_charfield_disabled(self):
        f = CharField(disabled=True)
        self.assertWidgetRendersTo(
            f, '<input type="text" name="f" id="id_f" disabled required>'
        )