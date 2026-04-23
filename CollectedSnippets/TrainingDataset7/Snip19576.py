def test_composite_pk_cannot_include_same_field(self):
        class Foo(models.Model):
            pass

        class Bar(models.Model):
            pk = models.CompositePrimaryKey("foo", "foo_id")
            foo = models.ForeignKey(Foo, on_delete=models.CASCADE)
            id = models.SmallIntegerField()

        self.assertEqual(Foo.check(databases=self.databases), [])
        self.assertEqual(
            Bar.check(databases=self.databases),
            [
                checks.Error(
                    "'foo_id' cannot be included in the composite primary key.",
                    hint="'foo_id' and 'foo' are the same fields.",
                    obj=Bar,
                    id="models.E042",
                ),
            ],
        )