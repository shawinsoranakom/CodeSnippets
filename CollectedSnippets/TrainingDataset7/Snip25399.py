def test_check_constraint_pointing_to_pk(self):
        class Model(models.Model):
            age = models.SmallIntegerField()

            class Meta:
                constraints = [
                    models.CheckConstraint(
                        name="name",
                        condition=models.Q(pk__gt=5) & models.Q(age__gt=models.F("pk")),
                    ),
                ]

        self.assertEqual(Model.check(databases=self.databases), [])