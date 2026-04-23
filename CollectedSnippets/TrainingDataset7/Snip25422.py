def test_unique_constraint_include_pointing_to_fk(self):
        class Target(models.Model):
            pass

        class Model(models.Model):
            fk_1 = models.ForeignKey(Target, models.CASCADE, related_name="target_1")
            fk_2 = models.ForeignKey(Target, models.CASCADE, related_name="target_2")

            class Meta:
                constraints = [
                    models.UniqueConstraint(
                        fields=["id"],
                        include=["fk_1_id", "fk_2"],
                        name="name",
                    ),
                ]

        self.assertEqual(Model.check(databases=self.databases), [])