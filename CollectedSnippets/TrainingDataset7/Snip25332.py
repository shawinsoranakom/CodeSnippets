def test_func_index_pointing_to_non_local_field(self):
        class Foo(models.Model):
            field1 = models.CharField(max_length=15)

        class Bar(Foo):
            class Meta:
                indexes = [models.Index(Lower("field1"), name="name")]

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