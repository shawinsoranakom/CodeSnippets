def test_index_include_pointing_to_non_local_field(self):
        class Parent(models.Model):
            field1 = models.IntegerField()

        class Child(Parent):
            field2 = models.IntegerField()

            class Meta:
                indexes = [
                    models.Index(fields=["field2"], include=["field1"], name="name"),
                ]

        self.assertEqual(
            Child.check(databases=self.databases),
            [
                Error(
                    "'indexes' refers to field 'field1' which is not local to "
                    "model 'Child'.",
                    hint="This issue may be caused by multi-table inheritance.",
                    obj=Child,
                    id="models.E016",
                ),
            ],
        )