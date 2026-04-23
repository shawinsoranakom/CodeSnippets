def test_bad_validators(self):
        class Model(models.Model):
            field = models.CharField(max_length=10, validators=[True])

        field = Model._meta.get_field("field")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "All 'validators' must be callable.",
                    hint=(
                        "validators[0] (True) isn't a function or instance of a "
                        "validator class."
                    ),
                    obj=field,
                    id="fields.E008",
                ),
            ],
        )