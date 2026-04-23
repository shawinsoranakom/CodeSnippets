def test_to_field_to_composite_primery_key(self):
        class Parent(models.Model):
            pk = models.CompositePrimaryKey("version", "name")
            version = models.IntegerField()
            name = models.CharField(max_length=20)

        class Child(models.Model):
            parent = models.ForeignKey(Parent, on_delete=models.CASCADE, to_field="pk")

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