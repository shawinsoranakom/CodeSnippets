def test_field_with_choices(self):
        self.assertFormfield(Member, "gender", forms.Select)