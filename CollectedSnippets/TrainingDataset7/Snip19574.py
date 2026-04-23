def test_composite_pk_cannot_include_nullable_field(self):
        class Foo(models.Model):
            pk = models.CompositePrimaryKey("foo_id", "id")
            foo_id = models.IntegerField()
            id = models.IntegerField(null=True)

        self.assertEqual(
            Foo.check(databases=self.databases),
            [
                checks.Error(
                    "'id' cannot be included in the composite primary key.",
                    hint="'id' field may not set 'null=True'.",
                    obj=Foo,
                    id="models.E042",
                ),
            ],
        )