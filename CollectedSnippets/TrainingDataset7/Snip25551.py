def test_many_to_many_from_model_with_composite_primary_key(self):
        class Parent(models.Model):
            name = models.CharField(max_length=20)

            class Meta:
                app_label = "invalid_models_tests"

        class Child(models.Model):
            pk = models.CompositePrimaryKey("version", "name")
            version = models.IntegerField()
            name = models.CharField(max_length=20)
            parents = models.ManyToManyField(Parent)

            class Meta:
                app_label = "invalid_models_tests"

        error = (
            "Field defines a relation involving model 'Child' which has a "
            "CompositePrimaryKey and such relations are not supported."
        )
        field = Child._meta.get_field("parents")
        self.assertEqual(
            field.check(from_model=Child),
            [Error(error, obj=field, id="fields.E347")],
        )