def test_proxy_model_does_not_check_superclass_composite_pk_errors(self):
        class Foo(models.Model):
            pk = models.CompositePrimaryKey("a", "b")
            a = models.SmallIntegerField()

        class Bar(Foo):
            class Meta:
                proxy = True

        self.assertEqual(
            Foo.check(databases=self.databases),
            [
                checks.Error(
                    "'b' cannot be included in the composite primary key.",
                    hint="'b' is not a valid field.",
                    obj=Foo,
                    id="models.E042",
                ),
            ],
        )
        self.assertEqual(Bar.check(databases=self.databases), [])