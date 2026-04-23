def test_composite_pk_must_not_have_other_pk_field(self):
        class Foo(models.Model):
            pk = models.CompositePrimaryKey("foo_id", "id")
            foo_id = models.IntegerField()
            id = models.IntegerField(primary_key=True)

        self.assertEqual(
            Foo.check(databases=self.databases),
            [
                checks.Error(
                    "The model cannot have more than one field with "
                    "'primary_key=True'.",
                    obj=Foo,
                    id="models.E026",
                ),
            ],
        )