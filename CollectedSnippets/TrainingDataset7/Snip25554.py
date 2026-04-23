def test_foreign_key_to_partially_unique_field(self):
        class Target(models.Model):
            source = models.IntegerField()

            class Meta:
                constraints = [
                    models.UniqueConstraint(
                        fields=["source"],
                        name="tfktpuf_partial_unique",
                        condition=models.Q(pk__gt=2),
                    ),
                ]

        class Model(models.Model):
            field = models.ForeignKey(Target, models.CASCADE, to_field="source")

        field = Model._meta.get_field("field")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "'Target.source' must be unique because it is referenced by a "
                    "foreign key.",
                    hint=(
                        "Add unique=True to this field or add a UniqueConstraint "
                        "(without condition) in the model Meta.constraints."
                    ),
                    obj=field,
                    id="fields.E311",
                ),
            ],
        )