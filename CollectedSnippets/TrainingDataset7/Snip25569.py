def test_to_fields_with_composite_primary_key(self):
        class Parent(models.Model):
            pk = models.CompositePrimaryKey("version", "name")
            version = models.IntegerField()
            name = models.CharField(max_length=20)

        class Child(models.Model):
            a = models.IntegerField()
            b = models.IntegerField()
            parent = models.ForeignObject(
                Parent,
                on_delete=models.SET_NULL,
                from_fields=("a", "b"),
                to_fields=("pk", "version"),
            )

        field = Child._meta.get_field("parent")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "Field defines a relation involving model 'Parent' which has a "
                    "CompositePrimaryKey and such relations are not supported.",
                    obj=field,
                    id="fields.E347",
                ),
            ],
        )