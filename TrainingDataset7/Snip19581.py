def test_composite_pk_cannot_include_generated_field(self):
        class Foo(models.Model):
            pk = models.CompositePrimaryKey("id", "foo")
            id = models.IntegerField()
            foo = models.GeneratedField(
                expression=F("id"),
                output_field=models.IntegerField(),
                db_persist=connection.features.supports_stored_generated_columns,
            )

        self.assertEqual(
            Foo.check(databases=self.databases),
            [
                checks.Error(
                    "'foo' cannot be included in the composite primary key.",
                    hint="'foo' field is a generated field.",
                    obj=Foo,
                    id="models.E042",
                ),
            ],
        )