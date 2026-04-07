def test_composite_pk_cannot_include_non_local_field(self):
        class Foo(models.Model):
            a = models.SmallIntegerField()

        class Bar(Foo):
            pk = models.CompositePrimaryKey("a", "b")
            b = models.SmallIntegerField()

        self.assertEqual(Foo.check(databases=self.databases), [])
        self.assertEqual(
            Bar.check(databases=self.databases),
            [
                checks.Error(
                    "'a' cannot be included in the composite primary key.",
                    hint="'a' field is not a local field.",
                    obj=Bar,
                    id="models.E042",
                ),
            ],
        )