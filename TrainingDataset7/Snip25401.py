def test_check_constraint_pointing_to_joined_fields(self):
        class Model(models.Model):
            name = models.CharField(max_length=10)
            field1 = models.PositiveSmallIntegerField()
            field2 = models.PositiveSmallIntegerField()
            field3 = models.PositiveSmallIntegerField()
            parent = models.ForeignKey("self", models.CASCADE)
            previous = models.OneToOneField("self", models.CASCADE, related_name="next")

            class Meta:
                constraints = [
                    models.CheckConstraint(
                        name="name1",
                        condition=models.Q(
                            field1__lt=models.F("parent__field1")
                            + models.F("parent__field2")
                        ),
                    ),
                    models.CheckConstraint(
                        name="name2", condition=models.Q(name=Lower("parent__name"))
                    ),
                    models.CheckConstraint(
                        name="name3",
                        condition=models.Q(parent__field3=models.F("field1")),
                    ),
                    models.CheckConstraint(
                        name="name4",
                        condition=models.Q(name=Lower("previous__name")),
                    ),
                ]

        joined_fields = [
            "parent__field1",
            "parent__field2",
            "parent__field3",
            "parent__name",
            "previous__name",
        ]
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