def test_formfield(self):
        no_choices_formfield = self.no_choices.formfield()
        self.assertIsInstance(no_choices_formfield, forms.IntegerField)
        fields = (
            self.empty_choices,
            self.empty_choices_bool,
            self.empty_choices_text,
            self.with_choices,
            self.with_choices_dict,
            self.with_choices_nested_dict,
            self.choices_from_enum,
            self.choices_from_iterator,
            self.choices_from_callable,
        )
        for field in fields:
            with self.subTest(field=field):
                self.assertIsInstance(field.formfield(), forms.ChoiceField)