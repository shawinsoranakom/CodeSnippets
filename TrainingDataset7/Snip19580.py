def test_composite_pk_must_be_named_pk(self):
        class Foo(models.Model):
            primary_key = models.CompositePrimaryKey("foo_id", "id")
            foo_id = models.IntegerField()
            id = models.IntegerField()

        self.assertEqual(
            Foo.check(databases=self.databases),
            [
                checks.Error(
                    "'CompositePrimaryKey' must be named 'pk'.",
                    obj=Foo._meta.get_field("primary_key"),
                    id="fields.E013",
                ),
            ],
        )