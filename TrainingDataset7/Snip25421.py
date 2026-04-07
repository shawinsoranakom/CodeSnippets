def test_unique_constraint_include_pointing_to_non_local_field(self):
        class Parent(models.Model):
            field1 = models.IntegerField()

        class Child(Parent):
            field2 = models.IntegerField()

            class Meta:
                constraints = [
                    models.UniqueConstraint(
                        fields=["field2"],
                        include=["field1"],
                        name="name",
                    ),
                ]

        self.assertEqual(
            Child.check(databases=self.databases),
            [
                Error(
                    "'constraints' refers to field 'field1' which is not local to "
                    "model 'Child'.",
                    hint="This issue may be caused by multi-table inheritance.",
                    obj=Child,
                    id="models.E016",
                ),
            ],
        )