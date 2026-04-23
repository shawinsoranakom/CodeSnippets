def test_check_constraint_pointing_to_fk(self):
        class Target(models.Model):
            pass

        class Model(models.Model):
            fk_1 = models.ForeignKey(Target, models.CASCADE, related_name="target_1")
            fk_2 = models.ForeignKey(Target, models.CASCADE, related_name="target_2")

            class Meta:
                constraints = [
                    models.CheckConstraint(
                        name="name",
                        condition=models.Q(fk_1_id=2) | models.Q(fk_2=2),
                    ),
                ]

        self.assertEqual(Model.check(databases=self.databases), [])