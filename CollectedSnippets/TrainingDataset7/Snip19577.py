def test_composite_pk_cannot_include_composite_pk_field(self):
        class Foo(models.Model):
            pk = models.CompositePrimaryKey("id", "pk")
            id = models.SmallIntegerField()

        self.assertEqual(
            Foo.check(databases=self.databases),
            [
                checks.Error(
                    "'pk' cannot be included in the composite primary key.",
                    hint="'pk' field has no column.",
                    obj=Foo,
                    id="models.E042",
                ),
            ],
        )