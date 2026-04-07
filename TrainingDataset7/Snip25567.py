def test_to_fields_exist(self):
        class Parent(models.Model):
            pass

        class Child(models.Model):
            a = models.PositiveIntegerField()
            b = models.PositiveIntegerField()
            parent = models.ForeignObject(
                Parent,
                on_delete=models.SET_NULL,
                from_fields=("a", "b"),
                to_fields=("a", "b"),
            )

        field = Child._meta.get_field("parent")
        self.assertEqual(
            field.check(),
            [
                Error(
                    "The to_field 'a' doesn't exist on the related model "
                    "'invalid_models_tests.Parent'.",
                    obj=field,
                    id="fields.E312",
                ),
                Error(
                    "The to_field 'b' doesn't exist on the related model "
                    "'invalid_models_tests.Parent'.",
                    obj=field,
                    id="fields.E312",
                ),
            ],
        )