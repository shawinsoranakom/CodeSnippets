def test_choicefield_disabled(self):
        f = ChoiceField(choices=[("J", "John"), ("P", "Paul")], disabled=True)
        self.assertWidgetRendersTo(
            f,
            '<select id="id_f" name="f" disabled><option value="J">John</option>'
            '<option value="P">Paul</option></select>',
        )