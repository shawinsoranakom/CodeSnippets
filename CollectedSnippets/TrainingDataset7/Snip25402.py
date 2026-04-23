def test_check_constraint_pointing_to_joined_fields_complex_check(self):
        class Model(models.Model):
            name = models.PositiveSmallIntegerField()
            field1 = models.PositiveSmallIntegerField()
            field2 = models.PositiveSmallIntegerField()
            parent = models.ForeignKey("self", models.CASCADE)

            class Meta:
                constraints = [
                    models.CheckConstraint(
                        name="name",
                        condition=models.Q(
                            (
                                models.Q(name="test")
                                & models.Q(field1__lt=models.F("parent__field1"))
                            )
                            | (
                                models.Q(name__startswith=Lower("parent__name"))
                                & models.Q(
                                    field1__gte=(
                                        models.F("parent__field1")
                                        + models.F("parent__field2")
                                    )
                                )
                            )
                        )
                        | (models.Q(name="test1")),
                    ),
                ]

        joined_fields = ["parent__field1", "parent__field2", "parent__name"]
        errors = Model.check(databases=self.databases)
        expected_errors = [
            Error(
                "'constraints' refers to the joined field '%s'." % field_name,
                obj=Model,
                id="models.E041",
            )
            for field_name in joined_fields
        ]
        self.assertCountEqual(errors, expected_errors)