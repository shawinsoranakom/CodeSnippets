def test_composite_pk_cannot_include_db_column(self):
        class Foo(models.Model):
            pk = models.CompositePrimaryKey("foo", "bar")
            foo = models.SmallIntegerField(db_column="foo_id")
            bar = models.SmallIntegerField(db_column="bar_id")

        class Bar(models.Model):
            pk = models.CompositePrimaryKey("foo_id", "bar_id")
            foo = models.SmallIntegerField(db_column="foo_id")
            bar = models.SmallIntegerField(db_column="bar_id")

        self.assertEqual(Foo.check(databases=self.databases), [])
        self.assertEqual(
            Bar.check(databases=self.databases),
            [
                checks.Error(
                    "'foo_id' cannot be included in the composite primary key.",
                    hint="'foo_id' is not a valid field.",
                    obj=Bar,
                    id="models.E042",
                ),
                checks.Error(
                    "'bar_id' cannot be included in the composite primary key.",
                    hint="'bar_id' is not a valid field.",
                    obj=Bar,
                    id="models.E042",
                ),
            ],
        )