def test_foreign_key_to_non_unique_field_under_explicit_model(self):
        class Target(models.Model):
            bad = models.IntegerField()

        class Model(models.Model):
            field = models.ForeignKey(Target, models.CASCADE, to_field="bad")

        field = Model._meta.get_field("field")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "'Target.bad' must be unique because it is referenced by a foreign "
                    "key.",
                    hint=(
                        "Add unique=True to this field or add a UniqueConstraint "
                        "(without condition) in the model Meta.constraints."
                    ),
                    obj=field,
                    id="fields.E311",
                ),
            ],
        )