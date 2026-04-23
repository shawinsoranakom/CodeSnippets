def test_foreign_key_to_unique_field_with_meta_constraint(self):
        class Target(models.Model):
            source = models.IntegerField()

            class Meta:
                constraints = [
                    models.UniqueConstraint(
                        fields=["source"],
                        name="tfktufwmc_unique",
                    ),
                ]

        class Model(models.Model):
            field = models.ForeignKey(Target, models.CASCADE, to_field="source")

        field = Model._meta.get_field("field")
        self.assertEqual(field.check(), [])