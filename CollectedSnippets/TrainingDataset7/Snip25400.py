def test_check_constraint_pointing_to_non_local_field(self):
        class Parent(models.Model):
            field1 = models.IntegerField()

        class Child(Parent):
            pass

            class Meta:
                constraints = [
                    models.CheckConstraint(name="name", condition=models.Q(field1=1)),
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