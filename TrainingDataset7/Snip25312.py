def test_pointing_to_non_local_field(self):
        class Foo(models.Model):
            field1 = models.IntegerField()

        class Bar(Foo):
            field2 = models.IntegerField()

            class Meta:
                indexes = [models.Index(fields=["field2", "field1"], name="name")]

        self.assertEqual(
            Bar.check(databases=self.databases),
            [
                Error(
                    "'indexes' refers to field 'field1' which is not local to "
                    "model 'Bar'.",
                    hint="This issue may be caused by multi-table inheritance.",
                    obj=Bar,
                    id="models.E016",
                ),
            ],
        )