def test_check_constraint_pointing_to_composite_primary_key(self):
        class Model(models.Model):
            pk = models.CompositePrimaryKey("version", "name")
            version = models.IntegerField()
            name = models.CharField(max_length=20)

            class Meta:
                constraints = [
                    models.CheckConstraint(
                        name="name",
                        condition=models.Q(pk__gt=(7, "focal")),
                    ),
                ]

        self.assertEqual(
            Model.check(databases=self.databases),
            [
                Error(
                    "'constraints' refers to a CompositePrimaryKey 'pk', but "
                    "CompositePrimaryKeys are not permitted in 'constraints'.",
                    obj=Model,
                    id="models.E048",
                ),
            ],
        )