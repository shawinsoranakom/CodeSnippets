def test_sanity_check_to(self):
        field = models.ForeignKey(UnicodeModel, models.CASCADE)
        with self.assertRaisesMessage(
            ValueError,
            'Model fields in "ModelState.fields" cannot refer to a model class - '
            '"app.Model.field.to" does. Use a string reference instead.',
        ):
            ModelState("app", "Model", [("field", field)])