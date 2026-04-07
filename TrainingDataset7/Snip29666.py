def test_model_field_choices(self):
        model_field = ArrayField(models.IntegerField(choices=((1, "A"), (2, "B"))))
        form_field = model_field.formfield()
        self.assertEqual(form_field.clean("1,2"), [1, 2])