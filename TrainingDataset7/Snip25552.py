def test_foreign_key_to_non_unique_field(self):
        class Target(models.Model):
            bad = models.IntegerField()  # No unique=True

        class Model(models.Model):
            foreign_key = models.ForeignKey("Target", models.CASCADE, to_field="bad")

        field = Model._meta.get_field("foreign_key")
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