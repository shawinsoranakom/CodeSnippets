def test_many_to_many_to_model_with_composite_primary_key(self):
        class Parent(models.Model):
            pk = models.CompositePrimaryKey("version", "name")
            version = models.IntegerField()
            name = models.CharField(max_length=20)

        class Child(models.Model):
            rel_class_parent = models.ManyToManyField(
                Parent, related_name="child_class_set"
            )
            rel_string_parent = models.ManyToManyField(
                "Parent", related_name="child_string_set"
            )

        error = (
            "Field defines a relation involving model 'Parent' which has a "
            "CompositePrimaryKey and such relations are not supported."
        )
        field = Child._meta.get_field("rel_string_parent")
        self.assertEqual(
            field.check(from_model=Child),
            [Error(error, obj=field, id="fields.E347")],
        )
        field = Child._meta.get_field("rel_class_parent")
        self.assertEqual(
            field.check(from_model=Child),
            [Error(error, obj=field, id="fields.E347")],
        )