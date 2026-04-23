def test_sanity_check_through(self):
        field = models.ManyToManyField("UnicodeModel")
        field.remote_field.through = UnicodeModel
        with self.assertRaisesMessage(
            ValueError,
            'Model fields in "ModelState.fields" cannot refer to a model class - '
            '"app.Model.field.through" does. Use a string reference instead.',
        ):
            ModelState("app", "Model", [("field", field)])